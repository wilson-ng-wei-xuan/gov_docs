# import json
# import pytest
# from datetime import datetime
# from typing import Any, Dict, List
# from aibots.aws_lambda.parser import RAGParser
# from aibots.aws_lambda.chunker import RAGChunker
# from aibots.aws_lambda.embedder import RAGEmbedder
# from ....parse.html.lambda_function import html_parser
# from ....parse.docx.lambda_function import docx_parser
# from ....parse.xlsx.lambda_function import xlsx_parser
# from ....parse.csv.lambda_function import csv_parser
# from ....parse.pptx.lambda_function import pptx_parser
# from ....parse.txt.lambda_function import txt_parser
# from ....parse.pdf.lambda_function import pdf_parser
# from ....chunk.fixed_chunker.lambda_function import chunk_docs as fixed_chunker
# from ....chunk.dataframe_clustering_chunker.lambda_function import chunk_docs as df_chunker
# from ....chunk.text_semantic_chunker.lambda_function import chunk_docs as semantic_chunker
# from ....embed.cohere.lambda_function import BedRockEmbedder
# from aibots.aws_lambda.models.rag import (
#     SQSRAGPipelineMessage, ExecutionState, SQSRAGConfigs)
# from aibots.aws_lambda.models.sqs import (SQSMessage, SQSMessageRecord)


# from typing import Dict, Any
# import pytest
# from aibots.aws_lambda.models.rag import (
#     ParseConfig,
#     ParseableFileType,
#     FixedChunker,
#     DataframeChunker,
#     SemanticChunker,
#     StoreConfig,
#     EmbedderConfig,
#     StoreOptions,
#     SQSRAGConfigs
# )
# from aibots.aws_lambda.models.sqs import (
#     SQSMessageRecord,
#     SQSMessageHandler,
#     SQSMessage
# )

# BUCKET_NAME = "s3-sitezapp-aibots-471112510129-project"
# BOT_NAME = "tests"
# CHUNK_SIZE = 5
# CHUNK_OVERLAP = 5
# MIN_CLUSTER_SIZE = 3
# OPENSEARCH_HOST = ""
# OPENSEARCH_INDEX_NAME = ""


# @pytest.fixture
# def html_fixed_cohere_opensearch_config(parse_html_config,
#                                         chunk_fixed_config,
#                                         embed_cohere_config,
#                                         store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_html_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def html_dataframe_cohere_opensearch_config(parse_html_config,
#                                             chunk_dataframe_config,
#                                             embed_cohere_config,
#                                             store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_html_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def html_semantic_cohere_opensearch_config(parse_html_config,
#                                            chunk_semantic_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_html_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_fixed_cohere_opensearch_config(parse_csv_config,
#                                        chunk_fixed_config,
#                                        embed_cohere_config,
#                                        store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_dataframe_cohere_opensearch_config(parse_csv_config,
#                                            chunk_dataframe_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_semantic_cohere_opensearch_config(parse_csv_config,
#                                           chunk_semantic_config,
#                                           embed_cohere_config,
#                                           store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def xlsx_fixed_cohere_opensearch_config(parse_xlsx_config,
#                                         chunk_fixed_config,
#                                         embed_cohere_config,
#                                         store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_xlsx_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def xlsx_dataframe_cohere_opensearch_config(parse_xlsx_config,
#                                             chunk_dataframe_config,
#                                             embed_cohere_config,
#                                             store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_xlsx_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def xlsx_semantic_cohere_opensearch_config(parse_xlsx_config,
#                                            chunk_semantic_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_xlsx_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pdf_fixed_cohere_opensearch_config(parse_pdf_config,
#                                        chunk_fixed_config,
#                                        embed_cohere_config,
#                                        store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pdf_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pdf_dataframe_cohere_opensearch_config(parse_pdf_config,
#                                            chunk_dataframe_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pdf_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pdf_semantic_cohere_opensearch_config(parse_pdf_config,
#                                           chunk_semantic_config,
#                                           embed_cohere_config,
#                                           store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pdf_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def docx_fixed_cohere_opensearch_config(parse_docx_config,
#                                         chunk_fixed_config,
#                                         embed_cohere_config,
#                                         store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_docx_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def docx_dataframe_cohere_opensearch_config(parse_docx_config,
#                                             chunk_dataframe_config,
#                                             embed_cohere_config,
#                                             store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_docx_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def docx_semantic_cohere_opensearch_config(parse_docx_config,
#                                            chunk_semantic_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_docx_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_fixed_cohere_opensearch_config(parse_csv_config,
#                                        chunk_fixed_config,
#                                        embed_cohere_config,
#                                        store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_dataframe_cohere_opensearch_config(parse_csv_config,
#                                            chunk_dataframe_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:

#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def csv_semantic_cohere_opensearch_config(parse_csv_config,
#                                           chunk_semantic_config,
#                                           embed_cohere_config,
#                                           store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_csv_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pptx_fixed_cohere_opensearch_config(parse_pptx_config,
#                                         chunk_fixed_config,
#                                         embed_cohere_config,
#                                         store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pptx_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pptx_dataframe_cohere_opensearch_config(parse_pptx_config,
#                                             chunk_dataframe_config,
#                                             embed_cohere_config,
#                                             store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pptx_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def pptx_semantic_cohere_opensearch_config(parse_pptx_config,
#                                            chunk_semantic_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_pptx_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def txt_fixed_cohere_opensearch_config(parse_txt_config,
#                                        chunk_fixed_config,
#                                        embed_cohere_config,
#                                        store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_txt_config,
#         chunk=chunk_fixed_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def txt_dataframe_cohere_opensearch_config(parse_txt_config,
#                                            chunk_dataframe_config,
#                                            embed_cohere_config,
#                                            store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_txt_config,
#         chunk=chunk_dataframe_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def txt_semantic_cohere_opensearch_config(parse_txt_config,
#                                           chunk_semantic_config,
#                                           embed_cohere_config,
#                                           store_opensearch_cohere_config) -> Dict[str, Any]:
#     return SQSRAGConfigs(
#         parse=parse_txt_config,
#         chunk=chunk_semantic_config,
#         embed=embed_cohere_config,
#         store=store_opensearch_cohere_config
#     ).model_dump()


# @pytest.fixture
# def parse_html_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.HTML,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampledoc.html",
#         chunk_size=5
#     ).model_dump()


# @pytest.fixture
# def parse_pdf_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.PDF,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampledoc.pdf",

#         chunk_size=CHUNK_SIZE
#     ).model_dump()


# @pytest.fixture
# def parse_docx_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.DOCX,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampledoc.docx",

#         chunk_size=CHUNK_SIZE
#     ).model_dump()


# @pytest.fixture
# def parse_xlsx_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.XLSX,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampleexcel.xlsx",

#         chunk_size=None
#     ).model_dump()


# @pytest.fixture
# def parse_pptx_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.PPTX,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampledoc.pptx",

#         chunk_size=CHUNK_SIZE
#     ).model_dump()


# @pytest.fixture
# def parse_txt_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.TXT,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="exampledoc.txt",

#         chunk_size=None
#     ).model_dump()


# @pytest.fixture
# def parse_csv_config() -> Dict[str, Any]:
#     return ParseConfig(
#         type=ParseableFileType.CSV,
#         bucket=BUCKET_NAME,
#         bot=BOT_NAME,
#         file_key="examplecsv.csv",
#         chunk_size=None
#     ).model_dump()


# @pytest.fixture
# def chunk_fixed_config() -> Dict[str, Any]:
#     return FixedChunker(
#         type="fixed",
#         chunk_size=CHUNK_SIZE,
#         separator="\n",
#         chunk_overlap=CHUNK_OVERLAP
#     ).model_dump()


# @pytest.fixture
# def chunk_dataframe_config() -> Dict[str, Any]:
#     return DataframeChunker(
#         type="dataframe",
#         chunk_size=CHUNK_SIZE,
#         min_cluster_size=3,
#         analyze_full_excel="False"
#     ).model_dump()


# @pytest.fixture
# def chunk_semantic_config() -> Dict[str, Any]:
#     return SemanticChunker(
#         type="semantic",
#         chunk_size=CHUNK_SIZE

#     ).model_dump()


# @pytest.fixture
# def embed_cohere_config() -> Dict[str, Any]:
#     return EmbedderConfig(
#         type="cohere",
#         model="cohere.embed-english-v3"
#     ).model_dump()


# @pytest.fixture
# def store_opensearch_cohere_config() -> Dict[str, Any]:
#     return StoreConfig(
#         type=StoreOptions.OPENSEARCH,
#         host=OPENSEARCH_HOST,
#         index_name=OPENSEARCH_INDEX_NAME,
#         embedding_type="cohere"
#     ).model_dump()


# INIT_MOCK_EVENT = {
#     "Records": [
#         {
#             "messageId": "213e3fce-1b2e-42ff-9dd5-12d8f1b86163",
#             "receiptHandle": "AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
#             "body": json.dumps({
#                 "bot_id": "xxx",
#                 "document_id": "yyy",
#                 "process_start_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
#                 "process_last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
#                 "process_end_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
#                 "error_message": {},
#                 "execution_status": "completed",
#                 "configs": {
#                     "parse": {
#                         "bucket": "s3-sitezapp-aibots-471112510129-project",
#                         "bot": "tests",
#                         "file_key": "exampledoc.html",
#                         "type": "html",
#                         "chunk_size": None
#                     },
#                     "chunk": {
#                         "type": "fixed",
#                         "chunk_size": 5,
#                         "separator": "\n",
#                         "chunk_overlap": 5,

#                     },
#                     "embed": {
#                         "type": "cohere",
#                         "model": "cohere.embed-english-v3"
#                     },
#                     "store": {
#                         "type": "opensearch",
#                         "host": "string",
#                         "index_name": "string",
#                         "embedding_type": "cohere"
#                     },
#                 },
#                 "results": {
#                     "parse": None,
#                     "chunk": None,
#                     "embed": None,
#                     "store": None,
#                 }
#             }),
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-6684e6d3-6fb9fad5bad2e7f1bd11ca00;Parent=0f1b758a73ce5eaa;Sampled=0;Lineage=ac449cae:0",
#                 "SentTimestamp": "1719985876798",
#                 "SenderId": "AROAW3MD6NKYRHESX3DBJ:lambda-sitezapp-aibots-rag-source-zip",
#                 "ApproximateFirstReceiveTimestamp": "1719985876802"
#             },
#             "messageAttributes": {},
#             "md5OfMessageAttributes": None,
#             "md5OfBody": "853731de9e45ec50948df25ae3287521",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip",
#             "awsRegion": "ap-southeast-1"
#         }
#     ]
# }

# AWS_MESSAGE_ID = "213e3fce-1b2e-42ff-9dd5-12d8f1b86163"
# AWS_RECEIPT_HANDLE = "AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY="
# AWS_ATTRIBUTES = {
#     "ApproximateReceiveCount": "1",
#     "AWSTraceHeader": "Root=1-6684e6d3-6fb9fad5bad2e7f1bd11ca00;Parent=0f1b758a73ce5eaa;Sampled=0;Lineage=ac449cae:0",
#     "SentTimestamp": "1719985876798",
#     "SenderId": "AROAW3MD6NKYRHESX3DBJ:lambda-sitezapp-aibots-rag-source-zip",
#     "ApproximateFirstReceiveTimestamp": "1719985876802"
# }
# AWS_MESSAGE_ATTRIBUTES = {}
# AWS_MD5_OF_MESSAGE_ATTRIBUTES = None
# AWS_MD5_OF_BODY = "853731de9e45ec50948df25ae3287521"
# AWS_EVENT_SOURCE = "aws:sqs"
# AWS_EVENT_SOURCE_ARN = "arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip"
# AWS_AWS_REGION = "ap-southeast-1"

# BOT_ID = "de4ee41d-5569-4261-ad17-044147ae3a56"
# DOCUMENT_ID = "8285367a-6e83-49f8-9e94-ab8e8997fe4d"
# PROCESS_START_DATETIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
# PROCESS_LAST_UPDATED = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
# PROCESS_END_DATETIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
# ERROR_MESSAGE = {}
# EXECUTION_STATUS = ExecutionState.completed.value
# RESULTS = {
#     "parse": None,
#     "chunk": None,
#     "embed": None,
#     "store": None,
# }


# @pytest.fixture
# def pipeline_message_body_permutations(html_dataframe_cohere_opensearch_config,
#                                        html_fixed_cohere_opensearch_config,
#                                        html_semantic_cohere_opensearch_config,
#                                        csv_dataframe_cohere_opensearch_config,
#                                        csv_fixed_cohere_opensearch_config,
#                                        csv_semantic_cohere_opensearch_config,
#                                        xlsx_dataframe_cohere_opensearch_config,
#                                        xlsx_fixed_cohere_opensearch_config,
#                                        xlsx_semantic_cohere_opensearch_config,
#                                        pdf_dataframe_cohere_opensearch_config,
#                                        pdf_fixed_cohere_opensearch_config,
#                                        pdf_semantic_cohere_opensearch_config,
#                                        docx_dataframe_cohere_opensearch_config,
#                                        docx_fixed_cohere_opensearch_config,
#                                        docx_semantic_cohere_opensearch_config,
#                                        pptx_dataframe_cohere_opensearch_config,
#                                        pptx_fixed_cohere_opensearch_config,
#                                        pptx_semantic_cohere_opensearch_config,
#                                        txt_dataframe_cohere_opensearch_config,
#                                        txt_fixed_cohere_opensearch_config,
#                                        txt_semantic_cohere_opensearch_config) -> List[Dict[str, Any]]:
#     """
#     all pipeline permutations for testing
#     """
#     return [
#         SQSRAGPipelineMessage(
#             bot_id=BOT_ID,
#             document_id=DOCUMENT_ID,
#             process_end_datetime=PROCESS_END_DATETIME,
#             process_last_updated=PROCESS_LAST_UPDATED,
#             process_start_datetime=PROCESS_START_DATETIME,
#             error_message=ERROR_MESSAGE,
#             execution_status=EXECUTION_STATUS,
#             results=RESULTS,
#             configs=SQSRAGConfigs(**config)
#         ).model_dump()
#         for config in [
#             html_dataframe_cohere_opensearch_config,
#             html_fixed_cohere_opensearch_config,
#             html_semantic_cohere_opensearch_config,
#             csv_dataframe_cohere_opensearch_config,
#             csv_fixed_cohere_opensearch_config,
#             csv_semantic_cohere_opensearch_config,
#             xlsx_dataframe_cohere_opensearch_config,
#             xlsx_fixed_cohere_opensearch_config,
#             xlsx_semantic_cohere_opensearch_config,
#             # pdf_dataframe_cohere_opensearch_config,
#             pdf_fixed_cohere_opensearch_config,
#             # pdf_semantic_cohere_opensearch_config,
#             # docx_dataframe_cohere_opensearch_config,
#             docx_fixed_cohere_opensearch_config,
#             # docx_semantic_cohere_opensearch_config,
#             pptx_dataframe_cohere_opensearch_config,
#             pptx_fixed_cohere_opensearch_config,
#             pptx_semantic_cohere_opensearch_config,
#             txt_dataframe_cohere_opensearch_config,
#             txt_fixed_cohere_opensearch_config,
#             txt_semantic_cohere_opensearch_config
#         ]
#     ]


# @pytest.fixture
# def pipeline_aws_records(pipeline_message_body_permutations) -> List[Dict[str, Any]]:
#     return [{
#         "Records": [
#             {
#                 "messageId": AWS_MESSAGE_ID,
#                 "receiptHandle": AWS_RECEIPT_HANDLE,
#                 "body": json.dumps(perm),
#                 "attributes": AWS_ATTRIBUTES,
#                 "messageAttributes": AWS_MESSAGE_ATTRIBUTES,
#                 "md5OfMessageAttributes": AWS_MD5_OF_MESSAGE_ATTRIBUTES,
#                 "md5OfBody": AWS_MD5_OF_BODY,
#                 "eventSource": AWS_EVENT_SOURCE,
#                 "eventSourceARN": AWS_EVENT_SOURCE_ARN,
#                 "awsRegion": AWS_AWS_REGION
#             }
#         ]
#     } for perm in pipeline_message_body_permutations]

from functools import lru_cache
import os
from aibots.models.rags import RAGPipelineEnviron
environ: RAGPipelineEnviron | None = None


def test_rag_environs() -> None:
    environ = RAGPipelineEnviron()
    print("os.environ", os.environ)
    print("integration environ:", environ)

    assert True
    # parsers = {
    #     "html": html_parser,
    #     "pdf": pdf_parser,
    #     "xlsx": xlsx_parser,
    #     "csv": csv_parser,
    #     "docx": docx_parser,
    #     "txt": txt_parser,
    #     "pptx": pptx_parser,
    # }
    # chunkers = {
    #     "fixed": fixed_chunker,
    #     "dataframe": df_chunker,
    #     "semantic": semantic_chunker
    # }
    # embedders = {
    #     "cohere": BedRockEmbedder().create_embeddings
    # }
    # for records in pipeline_aws_records:
    #     # for each permutation, take the body and loads it
    #     body = json.loads(SQSMessage(**records).records[0].body)
    #     # pass it into pipeline message
    #     pipeline_message = SQSRAGPipelineMessage(**body)
    #     # get message config
    #     configs = pipeline_message.configs
    #     # get the types, pass types to choose parsers, chunkers, embedders
    #     parse_type, chunk_type, embed_type, store_type = configs.parse.type, configs.chunk.type, configs.embed.type, configs.store.type
    #     parser = RAGParser(event=records, context=None,
    #                        parser=parsers[parse_type])
    #     parse_success, parse_failed = parser.run()

    #     chunker = RAGChunker(event={"Records": parse_success},
    #                          context=None, chunker=chunkers[chunk_type])
    #     chunk_sucess, chunk_failed = chunker.run()

    #     embedder = RAGEmbedder(
    #         event={"Records": chunk_sucess}, context=None, embedder=embedders[embed_type])
    #     embed_success, embed_failed = embedder.run()
    #     print(embed_success)
    #     assert len(parse_failed) == 0
    #     assert len(chunk_failed) == 0
    #     assert len(embed_failed) == 0
