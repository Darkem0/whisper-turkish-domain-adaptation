import unittest

from whisper_adaptation.metrics import error_rate, normalize_turkish, score_pair
from whisper_adaptation.repeat_safe import suppress_repeated_ngrams
from whisper_adaptation.routing import choose_adapter
from whisper_adaptation.segmentation import Window, segmentation_condition


class ResearchTests(unittest.TestCase):
    def test_normalization_is_turkish_aware(self):
        self.assertEqual(normalize_turkish("Merhaba, TÜRKİYE!"), "merhaba türkiye")

    def test_wer_and_cer(self):
        result = score_pair("bir iki", "bir üç")
        self.assertEqual(result["raw_wer"], 0.5)
        self.assertGreater(result["raw_cer"], 0)

    def test_repeat_safe_decoder(self):
        self.assertEqual(suppress_repeated_ngrams("teşekkür ederim teşekkür ederim bilgi"), "teşekkür ederim bilgi")

    def test_domain_routing_is_explicit(self):
        self.assertEqual(choose_adapter("noisy", {"noisy": "adapter"}), "adapter")
        self.assertEqual(choose_adapter("clean", {}), "base")

    def test_vad_segmentation_condition_is_reproducible(self):
        result = segmentation_condition([Window(0, 1, 0.4), Window(1, 2, 0.1)], 0.2)
        self.assertEqual(result["active_windows"], 1)
        self.assertEqual(result["active_seconds"], 1)


if __name__ == "__main__":
    unittest.main()
