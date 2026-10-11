//! Original, safe-Rust protocol fixture for Tokio actor admission and shutdown.
//!
//! Validation status: source-reviewed against Tokio 1.48.0 documentation;
//! compilation and runtime tests have NOT been run. No sleeps, timers, network,
//! unsafe code, or scheduler-exploration dependencies are used.

#![forbid(unsafe_code)]

use std::future::Future;
use tokio::sync::mpsc;

/// An admission failure retains the payload for the caller to inspect or retry.
#[derive(Debug)]
pub enum AdmissionError<T> {
    Cancelled(T),
    Closed(T),
}

/// Enqueues a message or returns ownership when cancellation/closure wins.
///
/// This fixture deliberately gives admission priority when both branches are
/// ready. That tie policy is application-specific, not a universal default.
/// No await occurs between obtaining the permit and consuming it with `send`.
/// `Ok(())` means enqueued, not processed or acknowledged.
pub async fn admit_or_cancel<T, C>(
    sender: &mpsc::Sender<T>,
    message: T,
    cancellation: C,
) -> Result<(), AdmissionError<T>>
where
    C: Future<Output = ()>,
{
    tokio::select! {
        biased;
        permit = sender.reserve() => {
            match permit {
                Ok(permit) => {
                    permit.send(message);
                    Ok(())
                }
                Err(_) => Err(AdmissionError::Closed(message)),
            }
        }
        () = cancellation => Err(AdmissionError::Cancelled(message)),
    }
}

#[cfg(test)]
mod tests {
    use super::{admit_or_cancel, AdmissionError};
    use std::future::{pending, ready};
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::Arc;
    use tokio::sync::mpsc::error::{TryRecvError, TrySendError};
    use tokio::sync::{mpsc, oneshot};

    #[derive(Debug)]
    struct Payload {
        id: u64,
        drops: Arc<AtomicUsize>,
    }

    impl Payload {
        fn new(id: u64, drops: &Arc<AtomicUsize>) -> Self {
            Self {
                id,
                drops: Arc::clone(drops),
            }
        }
    }

    impl Drop for Payload {
        fn drop(&mut self) {
            self.drops.fetch_add(1, Ordering::SeqCst);
        }
    }

    #[tokio::test(flavor = "current_thread")]
    async fn cancelled_direct_send_drops_its_unsent_payload() {
        // None fills the sole slot without contributing to the drop counter.
        let (tx, mut rx) = mpsc::channel::<Option<Payload>>(1);
        tx.send(None).await.unwrap();
        let drops = Arc::new(AtomicUsize::new(0));
        let payload = Payload::new(7, &drops);

        tokio::select! {
            biased;
            // Polled first, but the full queue makes admission pending.
            result = tx.send(Some(payload)) => {
                panic!("a full channel unexpectedly admitted a payload: {result:?}");
            }
            () = ready(()) => {}
        }

        // The losing send future owned the payload and has now dropped it.
        assert_eq!(drops.load(Ordering::SeqCst), 1);
        assert!(matches!(rx.recv().await, Some(None)));
        assert!(matches!(rx.try_recv(), Err(TryRecvError::Empty)));
    }

    #[tokio::test(flavor = "current_thread")]
    async fn cancelled_reservation_returns_payload_for_one_later_delivery() {
        let (tx, mut rx) = mpsc::channel::<Option<Payload>>(1);
        tx.send(None).await.unwrap();
        let drops = Arc::new(AtomicUsize::new(0));
        let payload = Payload::new(11, &drops);

        let recovered = match admit_or_cancel(&tx, Some(payload), ready(())).await {
            Err(AdmissionError::Cancelled(payload)) => payload,
            other => panic!("expected cancellation with ownership: {other:?}"),
        };

        assert_eq!(drops.load(Ordering::SeqCst), 0);
        assert_eq!(recovered.as_ref().unwrap().id, 11);
        assert!(matches!(rx.recv().await, Some(None)));
        assert!(matches!(rx.try_recv(), Err(TryRecvError::Empty)));

        // Free capacity and a never-ready cancellation make this retry ready.
        admit_or_cancel(&tx, recovered, pending()).await.unwrap();
        let received = rx.recv().await.unwrap().unwrap();
        assert_eq!(received.id, 11);
        assert!(matches!(rx.try_recv(), Err(TryRecvError::Empty)));
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        drop(received);
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[tokio::test(flavor = "current_thread")]
    async fn closed_admission_returns_the_original_payload() {
        let (tx, mut rx) = mpsc::channel(1);
        rx.close();
        let drops = Arc::new(AtomicUsize::new(0));
        let payload = Payload::new(13, &drops);

        let returned = match admit_or_cancel(&tx, payload, pending()).await {
            Err(AdmissionError::Closed(payload)) => payload,
            other => panic!("expected closed channel with ownership: {other:?}"),
        };
        assert_eq!(returned.id, 13);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        drop(returned);
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[derive(Debug)]
    struct Add {
        amount: u64,
        reply: oneshot::Sender<u64>,
    }

    async fn counter_actor(mut inbox: mpsc::Receiver<Add>) -> (u64, usize) {
        let mut total = 0_u64;
        let mut abandoned_replies = 0;
        while let Some(Add { amount, reply }) = inbox.recv().await {
            // Tiny fixed test inputs cannot overflow; this is a mock effect.
            total += amount;
            if reply.send(total).is_err() {
                // Reply abandonment does not roll back the already-applied add.
                abandoned_replies += 1;
            }
        }
        (total, abandoned_replies)
    }

    #[tokio::test(flavor = "current_thread")]
    async fn dropping_reply_receiver_does_not_retract_an_enqueued_request() {
        let (tx, inbox) = mpsc::channel(1);
        let (reply_tx, reply_rx) = oneshot::channel();
        tx.send(Add {
            amount: 23,
            reply: reply_tx,
        })
        .await
        .unwrap();
        drop(reply_rx);
        drop(tx);

        // Starting only now proves abandonment precedes every actor effect.
        let task = tokio::spawn(counter_actor(inbox));
        assert_eq!(task.await.unwrap(), (23, 1));
    }

    #[tokio::test(flavor = "current_thread")]
    async fn outstanding_permit_can_send_after_close_and_delays_termination() {
        let (tx, mut rx) = mpsc::channel(1);
        let permit = tx.reserve().await.unwrap();
        rx.close();

        assert!(rx.is_closed());
        assert!(matches!(
            tx.try_send("new admission"),
            Err(TrySendError::Closed("new admission"))
        ));
        // Empty is different from disconnected: the permit can still send.
        assert!(matches!(rx.try_recv(), Err(TryRecvError::Empty)));

        permit.send("reserved before close");
        assert_eq!(rx.recv().await, Some("reserved before close"));
        assert_eq!(rx.recv().await, None);
    }

    #[tokio::test(flavor = "current_thread")]
    async fn dropping_outstanding_permit_also_allows_clean_termination() {
        let (tx, mut rx) = mpsc::channel::<u8>(1);
        let permit = tx.reserve().await.unwrap();
        rx.close();
        assert!(matches!(rx.try_recv(), Err(TryRecvError::Empty)));

        drop(permit);
        assert_eq!(rx.recv().await, None);
    }

    #[tokio::test(flavor = "current_thread")]
    async fn ready_admission_wins_the_documented_ready_cancellation_tie() {
        let (tx, mut rx) = mpsc::channel(1);
        admit_or_cancel(&tx, 29_u8, ready(())).await.unwrap();
        assert_eq!(rx.recv().await, Some(29));
    }
}
