#[cfg(test)]
mod tests {
    use regex_automata::{meta::Regex, Anchored, Input, Match};

    #[test]
    fn slicing_invents_a_word_boundary() {
        let re = Regex::new(r"\bcat\b").unwrap();
        let hay = "bobcat!";
        // Wrong behavior reproduced: slicing makes a non-word look standalone.
        assert!(re.is_match(&hay[3..6]));
        assert!(!re.is_match(Input::new(hay).span(3..6)));
    }

    #[test]
    fn spans_keep_original_byte_offsets() {
        let re = Regex::new("cat").unwrap();
        let hay = "xx cat yy";
        assert_eq!(re.find(&hay[3..6]), Some(Match::must(0, 0..3)));
        assert_eq!(re.find(Input::new(hay).span(3..6)), Some(Match::must(0, 3..6)));
    }

    #[test]
    fn cursor_anchoring_rejects_gaps_but_is_not_caret() {
        let re = Regex::new("cat").unwrap();
        let hay = "!cat";
        assert_eq!(re.find(hay), Some(Match::must(0, 1..4)));
        assert_eq!(re.find(Input::new(hay).anchored(Anchored::Yes)), None);
        assert_eq!(re.find(Input::new(hay).span(1..4).anchored(Anchored::Yes)), Some(Match::must(0, 1..4)));
        assert_eq!(Regex::new("^cat").unwrap().find(Input::new(hay).span(1..4)), None);
    }

    #[test]
    fn pattern_priority_is_not_longest_token() {
        let short_first = Regex::new_many(&["a", "ab"]).unwrap();
        let long_first = Regex::new_many(&["ab", "a"]).unwrap();
        assert_eq!(short_first.find("ab"), Some(Match::must(0, 0..1)));
        assert_eq!(long_first.find("ab"), Some(Match::must(0, 0..2)));
    }

    #[test]
    fn iterator_advances_over_empty_matches_without_splitting_utf8() {
        let re = Regex::new("").unwrap();
        let matches: Vec<_> = re.find_iter("é").collect();
        assert_eq!(matches, vec![Match::must(0, 0..0), Match::must(0, 2..2)]);
    }

    #[test]
    fn boolean_existence_does_not_define_the_greedy_span() {
        let re = Regex::new("a+").unwrap();
        assert!(re.is_match("aaa"));
        assert_eq!(re.find("aaa"), Some(Match::must(0, 0..3)));
    }
}
