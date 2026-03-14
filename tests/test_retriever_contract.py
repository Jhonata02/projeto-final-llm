from __future__ import annotations

import unittest
from unittest.mock import patch

from src.retriever import PDFIndexerRetriever


class FakeCollection:
    def query(self, **kwargs):
        return {
            "documents": [["Trecho de teste"]],
            "metadatas": [[{"source": "arquivo.pdf", "page": 1}]],
            "distances": [[0.1]],
            "ids": [["id-1"]],
        }


class RetrieverContractTests(unittest.TestCase):
    @patch("src.retriever.DocumentConverter")
    @patch("src.retriever.chromadb.PersistentClient")
    def test_retrieve_returns_metadata_key(self, mock_client, _mock_converter):
        fake_collection = FakeCollection()
        mock_client.return_value.get_or_create_collection.return_value = fake_collection

        retriever = PDFIndexerRetriever()
        hits = retriever.retrieve("frequencia minima", k=1)

        self.assertEqual(len(hits), 1)
        self.assertIn("metadata", hits[0])
        self.assertNotIn("meta", hits[0])
        self.assertEqual(hits[0]["metadata"]["source"], "arquivo.pdf")


if __name__ == "__main__":
    unittest.main()
