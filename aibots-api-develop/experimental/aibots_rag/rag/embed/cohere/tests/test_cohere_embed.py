import json
from lambda_function import (
    BedRockEmbedder,
    lambda_handler
)
from datetime import datetime

TEST_TEXT_1 = """
GovTech Singapore, officially the Government Technology Agency of Singapore, is a statutory board under the Ministry of Communications and Information dedicated to driving digital transformation across the public sector. It plays a central role in modernizing government processes and enhancing service delivery through technology, supporting the nation's Smart Nation vision. By developing and maintaining technical infrastructure such as data centers and cloud platforms, and implementing robust cybersecurity measures, GovTech ensures the efficient and secure provision of digital services.

Additionally, GovTech collaborates with various government agencies, private sector companies, and academic institutions to foster innovation and implement advanced technologies like artificial intelligence, data analytics, and the Internet of Things (IoT). It manages key public digital services and platforms, including the SingPass authentication system and MyInfo personal data platform, making government services more accessible and user-friendly. Through these efforts, GovTech Singapore is pivotal in improving public sector efficiency, enhancing service delivery, and advancing Singapore's digital economy.
"""

TEST_TEXT_2 = """
The Parliament of Singapore is the supreme legislative body of the Republic of Singapore, responsible for enacting laws, approving the budget, and scrutinizing the government's policies and administration. It operates under a unicameral system, meaning it has only one legislative chamber, and is composed of elected Members of Parliament (MPs), Non-Constituency Members of Parliament (NCMPs), and Nominated Members of Parliament (NMPs). General elections, held at least once every five years, determine the composition of the Parliament, with the People's Action Party (PAP) historically holding a significant majority since independence.

Parliamentary sessions involve debates on proposed legislation, budget discussions, and questioning of government ministers to ensure accountability and transparency. The Speaker of Parliament, elected from among the MPs, presides over these sessions, maintaining order and facilitating discussions. Committees within Parliament, such as the Public Accounts Committee and the Government Parliamentary Committees, delve deeper into specific issues and policies, providing detailed oversight and recommendations. Overall, the Parliament of Singapore plays a crucial role in shaping the nation's laws, governance, and public policies, ensuring democratic processes and checks and balances in the government.
"""
mock_event_object = {
    "Records": [
        {
            "messageId": "213e3fce-1b2e-42ff-9dd5-12d8f1b86163",
            "receiptHandle": "AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
            "body": json.dumps({
                "bot_id": "xxx",
                "document_id": "yyy",
                "process_start_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "process_last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "process_end_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "error_message": {},
                "execution_status": "completed",
                "configs": {
                    "parse": {
                        "type": "html",
                        "bucket": "s3-sitezapp-aibots-471112510129-project",
                        "bot": "tests",
                        "file_key": "exampledoc.html",
                        "chunk_size": None
                    },
                    "chunk": {
                        "type": "dataframe",
                        "chunk_size": 5,
                        "min_cluster_size": 5,
                        "analyze_full_excel": "False"
                    },
                    "embed": {
                        "type": "cohere",
                        "model": "cohere.embed-english-v3"
                    },

                    "store": {
                        "type": "opensearch",
                        "host": "string",
                        "index_name": "string",
                        "embedding_type": "cohere"
                    },
                },
                "results": {
                    "parse": [
                        {
                            "text": TEST_TEXT_1,
                            "metadata": {
                                "page_number": "1",
                                "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                            }
                        },
                        {
                            "text": TEST_TEXT_2,
                            "metadata": {
                                "page_number": "2",
                                "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                            }
                        }
                    ],
                    "chunk": [
                        {
                            "text": TEST_TEXT_1,
                            "chunk": 0,
                            "page_number": "1",
                            "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                        },
                        {
                            "text": TEST_TEXT_2,
                            "chunk": 1,
                            "page_number": "2",
                            "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                        }
                    ],
                    "embed": None,
                    "store": None,
                }
            }),
            "attributes": {
                "ApproximateReceiveCount": "1",
                "AWSTraceHeader": "Root=1-6684e6d3-6fb9fad5bad2e7f1bd11ca00;Parent=0f1b758a73ce5eaa;Sampled=0;Lineage=ac449cae:0",
                "SentTimestamp": "1719985876798",
                "SenderId": "AROAW3MD6NKYRHESX3DBJ:lambda-sitezapp-aibots-rag-source-zip",
                "ApproximateFirstReceiveTimestamp": "1719985876802"
            },
            "messageAttributes": {},
            "md5OfMessageAttributes": None,
            "md5OfBody": "853731de9e45ec50948df25ae3287521",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip",
            "awsRegion": "ap-southeast-1"
        }
    ]
}


def test_bedrock_cohere_embedder() -> None:
    embedder = BedRockEmbedder()
    response = embedder.create_embeddings(texts=[
        TEST_TEXT_1, TEST_TEXT_2
    ])
    assert all(isinstance(embed, list) for embed in response)
    for embed in response:
        all(isinstance(coord, float) for coord in embed)


def test_embed_lambda_handler() -> None:
    response = lambda_handler(event=mock_event_object, context=None)
