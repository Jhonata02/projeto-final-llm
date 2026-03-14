from __future__ import annotations

import unittest
from unittest.mock import patch

import src.pipeline as pipeline


class FakeRetriever:
    def __init__(self):
        self.ensure_calls = 0
        self.build_calls = 0

    def ensure_ready(self):
        self.ensure_calls += 1
        if self.ensure_calls == 1:
            raise RuntimeError("collection vazia")

    def build_index_from_folder(self, folder):
        self.build_calls += 1


class PipelineBootstrapTests(unittest.TestCase):
    def setUp(self):
        pipeline._retriever = None
        pipeline._app = None

    @patch("src.pipeline.PDFIndexerRetriever", return_value=FakeRetriever())
    def test_get_retriever_builds_index_when_collection_is_empty(self, _mock_retriever_cls):
        retriever = pipeline.get_retriever()
        self.assertEqual(retriever.build_calls, 1)
        self.assertEqual(retriever.ensure_calls, 2)


if __name__ == "__main__":
    unittest.main()
