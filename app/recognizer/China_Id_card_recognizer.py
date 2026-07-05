from presidio_analyzer import Pattern, PatternRecognizer


class ChinaIdCardRecognizer(PatternRecognizer):
    CN_ID_CARD_PATTERN = r'[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]'
    def __init__(self, supported_language: str) -> None:
        super().__init__(
            supported_entity="CN_ID_CARD",
            name=f"ChinaIdCardRecognizer_{supported_language}",
            supported_language=supported_language,
            patterns=[
                Pattern(
                    name="cn_id_card",
                    regex=ChinaIdCardRecognizer.CN_ID_CARD_PATTERN,
                    score=0.85,
                )
            ],
        )

    def validate_result(self, pattern_text: str) -> bool:
        """Validate an 18-digit Chinese mainland ID card number."""
        if len(pattern_text) != 18:
            return False

        weight: list[int] = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_code: list[str] = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

        total: int = 0
        for i in range(17):
            if not pattern_text[i].isdigit():
                return False
            total += int(pattern_text[i]) * weight[i]

        return pattern_text[17].upper() == check_code[total % 11]