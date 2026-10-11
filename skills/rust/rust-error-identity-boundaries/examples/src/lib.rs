//! Original, side-effect-free examples of error-identity boundaries.
//!
//! Source-reviewed against anyhow 1.0.104 and thiserror 2.0.21.
//! Neither compiled nor executed in the preparation environment.
//! The supplied Results simulate operations; no files or sockets are opened.

#![forbid(unsafe_code)]

use anyhow::{Context, Error};
use std::{fmt, io};

/// A typed context marker. Deliberately does not implement std::error::Error.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LoadingPolicy {
    pub policy: &'static str,
}

impl fmt::Display for LoadingPolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "loading policy {}", self.policy)
    }
}

/// An ordinary domain error with both operation data and a lower-level source.
/// #[from] cannot fill the additional policy field, so construction is explicit.
#[derive(Debug, thiserror::Error)]
#[error("cannot load policy {policy}")]
pub struct LoadFailure {
    pub policy: &'static str,
    #[source]
    pub source: io::Error,
}

pub fn attach_operation(
    policy: &'static str,
    result: Result<u8, io::Error>,
) -> anyhow::Result<u8> {
    result.context(LoadingPolicy { policy })
}

pub fn wrap_operation(
    policy: &'static str,
    result: Result<u8, io::Error>,
) -> Result<u8, LoadFailure> {
    result.map_err(|source| LoadFailure { policy, source })
}

/// Fixture policy: recognize missing inputs only during policy loading.
/// This is an example application decision, not a general recovery rule.
pub fn is_missing_policy(error: &Error) -> bool {
    error.is::<LoadingPolicy>()
        && error.chain().any(|cause| {
            cause
                .downcast_ref::<io::Error>()
                .is_some_and(|source| source.kind() == io::ErrorKind::NotFound)
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    fn simulated_error(kind: io::ErrorKind) -> io::Error {
        io::Error::new(kind, "synthetic failure")
    }

    // Deliberately wrong for the domain-wrapper case tested below.
    fn direct_only_classifier(error: &Error) -> bool {
        error.is::<LoadingPolicy>()
            && error
                .downcast_ref::<io::Error>()
                .is_some_and(|source| source.kind() == io::ErrorKind::NotFound)
    }

    fn wrapped_missing() -> Error {
        let domain = wrap_operation(
            "alpha",
            Err(simulated_error(io::ErrorKind::NotFound)),
        )
        .expect_err("the synthetic operation must fail");
        Error::new(domain).context(LoadingPolicy { policy: "alpha" })
    }

    #[test]
    fn typed_context_and_original_error_both_remain_downcastable() {
        let error = attach_operation(
            "alpha",
            Err(simulated_error(io::ErrorKind::NotFound)),
        )
        .context("preparing an in-memory configuration")
        .expect_err("the synthetic operation must fail");

        assert_eq!(
            error.downcast_ref::<LoadingPolicy>(),
            Some(&LoadingPolicy { policy: "alpha" })
        );
        assert_eq!(
            error.downcast_ref::<io::Error>().map(io::Error::kind),
            Some(io::ErrorKind::NotFound)
        );
        assert!(direct_only_classifier(&error));
        assert!(is_missing_policy(&error));
    }

    #[test]
    fn a_domain_wrapper_requires_explicit_source_chain_inspection() {
        let error = wrapped_missing().context("preparing configuration");

        assert!(error.downcast_ref::<LoadingPolicy>().is_some());
        assert!(error.downcast_ref::<LoadFailure>().is_some());
        assert!(error.downcast_ref::<io::Error>().is_none());

        // Failure: the direct-only implementation misses the wrapped cause.
        assert!(!direct_only_classifier(&error));
        // Remedy: the intended classifier inspects sources while retaining
        // the operation marker as a separate precondition.
        assert!(is_missing_policy(&error));
        assert_eq!(
            error.chain().find_map(|cause| {
                cause.downcast_ref::<io::Error>().map(io::Error::kind)
            }),
            Some(io::ErrorKind::NotFound)
        );
    }

    #[test]
    fn stringification_erases_types_and_causes_but_preservation_repairs_it() {
        let domain = wrap_operation(
            "alpha",
            Err(simulated_error(io::ErrorKind::NotFound)),
        )
        .expect_err("the synthetic operation must fail");

        // Deliberate bug: the useful domain error is replaced by its text.
        let erased = Error::msg(domain.to_string())
            .context(LoadingPolicy { policy: "alpha" });
        assert!(erased.is::<LoadingPolicy>());
        assert!(!erased.is::<LoadFailure>());
        assert!(!erased.is::<io::Error>());
        assert!(!erased.chain().any(|cause| cause.is::<io::Error>()));
        assert!(!is_missing_policy(&erased));

        // Preserve the original value instead. Its message is intentionally
        // unchanged; only checking the message would miss the original bug.
        let retained = Error::new(domain)
            .context(LoadingPolicy { policy: "alpha" });
        assert_eq!(erased.to_string(), retained.to_string());
        assert!(retained.is::<LoadFailure>());
        assert!(is_missing_policy(&retained));
    }

    #[test]
    fn explicit_map_err_retains_operation_fields_and_source() {
        let failure = wrap_operation(
            "beta",
            Err(simulated_error(io::ErrorKind::PermissionDenied)),
        )
        .expect_err("the synthetic operation must fail");

        assert_eq!(failure.policy, "beta");
        assert_eq!(failure.source.kind(), io::ErrorKind::PermissionDenied);
        let source = std::error::Error::source(&failure)
            .expect("the domain error must expose its source");
        assert_eq!(
            source.downcast_ref::<io::Error>().map(io::Error::kind),
            Some(io::ErrorKind::PermissionDenied)
        );
    }

    #[test]
    fn unrelated_and_different_kind_errors_are_negative_controls() {
        let unrelated = Error::new(simulated_error(io::ErrorKind::NotFound));
        assert!(!is_missing_policy(&unrelated));

        let denied = attach_operation(
            "alpha",
            Err(simulated_error(io::ErrorKind::PermissionDenied)),
        )
        .expect_err("the synthetic operation must fail");
        assert!(denied.is::<LoadingPolicy>());
        assert!(!is_missing_policy(&denied));
    }

    #[test]
    fn changing_human_context_does_not_change_classification() {
        let first = wrapped_missing().context("old wording");
        let second = wrapped_missing().context("new wording");
        assert_ne!(first.to_string(), second.to_string());
        assert!(is_missing_policy(&first));
        assert!(is_missing_policy(&second));
    }

    #[test]
    fn with_context_prepares_details_only_on_the_error_path() {
        let evaluations = Cell::new(0);
        let success: Result<u8, io::Error> = Ok(7);
        let success = success.with_context(|| {
            evaluations.set(evaluations.get() + 1);
            LoadingPolicy { policy: "alpha" }
        });
        assert_eq!(success.expect("the simulated success must survive"), 7);
        assert_eq!(evaluations.get(), 0);

        let failure: Result<u8, io::Error> =
            Err(simulated_error(io::ErrorKind::NotFound));
        let failure = failure.with_context(|| {
            evaluations.set(evaluations.get() + 1);
            LoadingPolicy { policy: "alpha" }
        });
        assert_eq!(evaluations.get(), 1);
        assert!(is_missing_policy(
            &failure.expect_err("the synthetic operation must fail")
        ));
    }
}
