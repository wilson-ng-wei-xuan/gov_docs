from typing import Dict, Any

import os

from moto import mock_aws
import boto3
import json

import pytest

from aibots.models.rags.internal import AIBotsPipelineMessage, RAGPipelineMessage, SQSMessageRecord, SourceResult, \
    ParseResult, Page

from aibots.models.knowledge_bases import KnowledgeBase

from aibots.models import RAGConfig

from aibots.models.knowledge_bases import KnowledgeBaseStorage


@pytest.fixture(scope="session")
def parsed_config() -> Dict[str, Any]:
    yield {
        "parse": {
            "chunk_size": 10
        }
    }


@pytest.fixture(scope="session")
def csv_parse_result() -> ParseResult:
    return ParseResult(
        pages=[Page(**page) for page in [{
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '2 ROOM', 'block': 172, 'street_name': 'ANG MO KIO AVE 4', 'storey_range': '06 TO 10', 'floor_area_sqm': 45, 'flat_model': 'Improved', 'lease_commence_date': 1986, 'resale_price': 250000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '2 ROOM', 'block': 510, 'street_name': 'ANG MO KIO AVE 8', 'storey_range': '01 TO 05', 'floor_area_sqm': 44, 'flat_model': 'Improved', 'lease_commence_date': 1980, 'resale_price': 265000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 610, 'street_name': 'ANG MO KIO AVE 4', 'storey_range': '06 TO 10', 'floor_area_sqm': 68, 'flat_model': 'New Generation', 'lease_commence_date': 1980, 'resale_price': 315000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 474, 'street_name': 'ANG MO KIO AVE 10', 'storey_range': '01 TO 05', 'floor_area_sqm': 67, 'flat_model': 'New Generation', 'lease_commence_date': 1984, 'resale_price': 320000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 604, 'street_name': 'ANG MO KIO AVE 5', 'storey_range': '06 TO 10', 'floor_area_sqm': 67, 'flat_model': 'New Generation', 'lease_commence_date': 1980, 'resale_price': 321000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 154, 'street_name': 'ANG MO KIO AVE 5', 'storey_range': '01 TO 05', 'floor_area_sqm': 68, 'flat_model': 'New Generation', 'lease_commence_date': 1981, 'resale_price': 321000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 110, 'street_name': 'ANG MO KIO AVE 4', 'storey_range': '01 TO 05', 'floor_area_sqm': 67, 'flat_model': 'New Generation', 'lease_commence_date': 1978, 'resale_price': 323000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}, {
            "text": "{\"file\": \"tests/examplecsv.csv\", \"data\": \"{'month': '2012-03', 'town': 'ANG MO KIO', 'flat_type': '3 ROOM', 'block': 445, 'street_name': 'ANG MO KIO AVE 10', 'storey_range': '01 TO 05', 'floor_area_sqm': 67, 'flat_model': 'New Generation', 'lease_commence_date': 1979, 'resale_price': 325000}\"}",
            "metadata": {"source": "tests/examplecsv.csv", "page_number": 0,
                         "last_update_date": "2024-07-30 06:30:29.000000"}}]]

    )


@pytest.fixture(scope="session")
def docx_parse_result() -> ParseResult:
    return ParseResult(pages=[
        Page(
            text="{File name: tests/exampledoc.docx, page: 1, content: In the context of interacting with an AI, a prompt refers to a piece of text or input provided by a user to initiate a response or action from the AI. A prompt can take many forms, such as a question, a statement, or a command, and is typically used to provide context or direction to the AI's response.}",
            metadata={"source": "tests/exampledoc.docx", "page_number": "1",
                      "last_update_date": "2024-07-30 06:35:33.000000"})]
    )


@pytest.fixture(scope="session")
def pptx_parse_result() -> ParseResult:
    return ParseResult(pages=[
        Page(
            text="{File name: tests/exampledoc.pptx, page: 1, content: OBS Singapore\\n\\nWhat is OBS?\\n\\nPlease refer to the link provided in Parents Gateway for the e-Registration. Do note that SingPass login is required. \\n\\nWhat is DEF?\\n\\nMOE-OBS Challenge Programme is open to ALL Secondary 3 students in 2023. }",
            metadata={"source": "tests/exampledoc.pptx", "page_number": "1",
                      "last_update_date": "2024-07-30 06:37:48.000000"})
    ])


@pytest.fixture(scope="session")
def pdf_parse_result() -> ParseResult:
    return ParseResult(pages=[
        Page(**page) for page in [{
            "text": "{File name: tests/exampledoc.pdf, page: 1, content: About OBS Registration/ General enquiries\\n\\n1) Where can I register for my child?\\n\\n2) When does the registration start?\\n\\n3) Is OBS open to all Secondary 3 students or only for selected students?\\n\\n4) Will my child be required to wear a mask at all times?\\n\\nAbout AI\\n\\nPlease refer to the link provided in Parents Gateway for the e-Registration. Do note that SingPass login is required. The e-Registration period is from 16 September to 7 October 2022.}",
            "metadata": {"source": "tests/exampledoc.pdf", "page_number": "1",
                         "last_update_date": "2024-07-30 06:39:30.000000"}}, {
            "text": "{File name: tests/exampledoc.pdf, page: 1, content: MOE-OBS Challenge Programme is open to ALL Secondary 3 students in 2023.\\n\\nWe will adhere to the national posture at the point in time when the MOE-OBS Challenge Programme is taking place. Based on the current status, mask wearing is optional.\\n\\n4) Will my child be required to wear a mask at all times?\\n\\nWe will adhere to the national posture at the point in time when the MOE-OBS Challenge Programme is taking place. Based on the current status, mask wearing is optional.}",
            "metadata": {"source": "tests/exampledoc.pdf", "page_number": "1",
                         "last_update_date": "2024-07-30 06:39:30.000000"}}, {
            "text": "{File name: tests/exampledoc.pdf, page: 2, content: In the context of interacting with an AI, a prompt refers to a piece of text or input provided by a user to initiate a response or action from the AI. A prompt can take many forms, such as a question, a statement, or a command, and is typically used to provide context or direction to the AI\'s response.}",
            "metadata": {"source": "tests/exampledoc.pdf", "page_number": "2",
                         "last_update_date": "2024-07-30 06:39:30.000000"}}]
    ])


@pytest.fixture(scope="session")
def xlsx_parse_result() -> ParseResult:
    return ParseResult(pages=[
        Page(**page) for page in [{
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'2 ROOM\', \'block\': 172, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 45, \'flat_model\': \'Improved\', \'lease_commence_date\': 1986, \'resale_price\': 250000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'2 ROOM\', \'block\': 510, \'street_name\': \'ANG MO KIO AVE 8\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 44, \'flat_model\': \'Improved\', \'lease_commence_date\': 1980, \'resale_price\': 265000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 610, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 315000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 474, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1984, \'resale_price\': 320000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 604, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 321000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 154, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 321000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 110, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 323000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 445, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 325000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 476, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 328000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 631, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1985, \'resale_price\': 330000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 155, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 331000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 560, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 332000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 561, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 333000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 405, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 333000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 548, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 335000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 126, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 336000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 558, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 336000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 212, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1977, \'resale_price\': 336000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 333, \'street_name\': \'ANG MO KIO AVE 1\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 338000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 114, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 339000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 151, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 339000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 503, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 340000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 230, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 340000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 157, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 69, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 342000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 604, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 342000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 213, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1976, \'resale_price\': 347000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 419, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 348000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 549, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'16 TO 20\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 350000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 201, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1977, \'resale_price\': 350000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 533, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 350000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 533, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 350000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 571, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 353000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 623, \'street_name\': \'ANG MO KIO AVE 9\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 355000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 465, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 357000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 119, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 358000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 121, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 360000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 418, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 363000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 607, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 68, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 367000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 216, \'street_name\': \'ANG MO KIO AVE 1\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1976, \'resale_price\': 368000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 103, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 368000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 570, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 368000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 127, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 368000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 159, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 368000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 121, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 370000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 173, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 83, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1982, \'resale_price\': 372000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 418, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 373000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 585, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 377000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 120, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 379000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 421, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 380000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 419, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 380000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 173, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 83, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1982, \'resale_price\': 380000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 178, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1981, \'resale_price\': 380000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 417, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 74, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 385000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 509, \'street_name\': \'ANG MO KIO AVE 8\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 81, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 385000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 128, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 67, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 390000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 328, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 392000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 463, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 398000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 561, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 398000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 623, \'street_name\': \'ANG MO KIO AVE 9\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 399000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 575, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 81, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 400000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 587, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1979, \'resale_price\': 400000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 114, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 88, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 400000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'4 ROOM\', \'block\': 218, \'street_name\': \'ANG MO KIO AVE 1\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1976, \'resale_price\': 400000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 320, \'street_name\': \'ANG MO KIO AVE 1\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1977, \'resale_price\': 403000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 348, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 411000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'4 ROOM\', \'block\': 601, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'01 TO 05\', \'floor_area_sqm\': 91, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 411000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 348, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 414000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 313, \'street_name\': \'ANG MO KIO AVE 3\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 73, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 418000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 523, \'street_name\': \'ANG MO KIO AVE 5\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1980, \'resale_price\': 426888}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'4 ROOM\', \'block\': 108, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 92, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 427000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'3 ROOM\', \'block\': 466, \'street_name\': \'ANG MO KIO AVE 10\', \'storey_range\': \'11 TO 15\', \'floor_area_sqm\': 82, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1984, \'resale_price\': 428000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}, {
            "text": "{File: exampleexcel.xlsx, data: {\'month\': \'2012-03\', \'town\': \'ANG MO KIO\', \'flat_type\': \'4 ROOM\', \'block\': 105, \'street_name\': \'ANG MO KIO AVE 4\', \'storey_range\': \'06 TO 10\', \'floor_area_sqm\': 92, \'flat_model\': \'New Generation\', \'lease_commence_date\': 1978, \'resale_price\': 430000}}",
            "metadata": {"source": "exampleexcel.xlsx", "page_number": 0,
                         "last_update_date": "2024-07-30 06:41:00.000000"}}]
    ])


@pytest.fixture(scope="session")
def html_parse_result() -> ParseResult:
    return ParseResult(pages=[Page(
        text="{File name: tests/exampledoc.html, page: 1, content: About Me\\n\\nHello! My name is John Doe, and this is my personal website. I love sharing my thoughts on various topics including technology, travel, and food.\\n\\nMy Interests\\n\\nTechnology\\n\\nTravel\\n\\nFood\\n\\nMy Favorite Websites\\n\\nExample\\n\\nSample\\n\\nTest\\n\\nGallery\\n\\nContact Me}",
        metadata={"source": "tests/exampledoc.html", "page_number": "1",
                  "last_update_date": "2024-07-30 06:45:53.000000"})])


@pytest.fixture(scope="session")
def txt_parse_result() -> ParseResult:
    return ParseResult(pages=[Page(
        text="About OBS\\n Registration/ General enquiries \\n\\n1) Where can I register for my child? \\n\\tPlease refer to the link provided in Parents Gateway for the e-Registration. Do note that SingPass login is required. \\n\\n2) When does the registration start? \\n\\tThe e-Registration period is from 16 September to 7 October 2022. \\n\\n3) Is OBS open to all Secondary 3 students or only for selected students? \\n\\tMOE-OBS Challenge Programme is open to ALL Secondary 3 students in 2023. \\n\\n4) Will my child be required to wear a mask at all times? \\n\\tWe will adhere to the national posture at the point in time when the MOE-OBS Challenge Programme is taking place. Based on the current status, mask wearing is optional. \\n\\nAbout AI\\n \\u2003\\n\\n4) Will my child be required to wear a mask at all times? \\n\\tWe will adhere to the national posture at the point in time when the MOE-OBS Challenge Programme is taking place. Based on the current status, mask wearing is optional. \\n\\n\\nIn the context of interacting with an AI, a prompt refers to a piece of text or input provided by a user to initiate a response or action from the AI. A prompt can take many forms, such as a question, a statement, or a command, and is typically used to provide context or direction to the AI\'s response.\\n\\n",
        metadata={"source": "tests/exampledoc.txt", "page_number": 0,
                  "last_update_date": "2024-07-30 06:50:44.000000"})])


@pytest.fixture(scope="session")
def semantic_chunk_config() -> Dict[str, Any]:
    yield {
        "chunk":
            {
                "type": "fixed",
                "chunk_size": 100,
                "chunk_overlap": 5,
                "separator": "\n"
            }
    }


@pytest.fixture(scope="session")
def text_len_1000() -> str:
    yield """Singapore's government has been a global leader in leveraging technology to improve public services,
    governance, and urban living. The country's Smart Nation initiative aims to harness data and digital technologies
    to enhance citizens' quality of life, boost economic competitiveness, and create a sustainable living environment.
    Key components include a nationwide sensor network, advanced data analytics, and AI-driven solutions. 
    Singapore's e-government services are highly integrated, offering seamless access to various public services 
    through platforms like SingPass and MyInfo. The government also prioritizes cybersecurity and data protection, 
    ensuring the safe use of digital services. Smart urban solutions, such as smart traffic management and predictive
    maintenance of public infrastructure, are implemented to optimize efficiency and sustainability. Overall, 
    Singapore's government technology strategy focuses on innovation, efficiency, and citizen-centric services, 
    positioning the city-state as a model for smart cities worldwide.Singapore's approach to government technology
    is multifaceted, encompassing various initiatives and """


@pytest.fixture(scope="session")
def semantic_chunk_config_size_100() -> Dict[str, Any]:
    yield {
        "chunk":
            {
                "type": "fixed",
                "chunk_size": 100,
                "chunk_overlap": 5,
                "separator": "\n"
            }
    }


@pytest.fixture(scope="session")
def event_body() -> AIBotsPipelineMessage:
    yield AIBotsPipelineMessage(
        Records=[]
    )


@pytest.fixture(scope="session")
def sqs_message() -> SQSMessageRecord:
    yield SQSMessageRecord(
        messageId="213e3fce1b2e42ff9dd512d8f1b86163",
        receiptHandle="AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
        body=json.dumps(RAGPipelineMessage(
            agent="dad32f1794b94153a2fd9997929a4280",
            knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
            knowledge_bases=[],
            pipeline=RAGConfig(config={}),
            results=[],
            supported_pipelines=[{}]
        ).model_dump(mode="json")),
        attributes={},
        messageAttributes={},
        md5OfMessage_attributes=None,
        md5OfBody="853731de9e45ec50948df25ae3287521",
        eventSourceARN="arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip",
        eventSource="aws:sqs",
        awsRegion="ap-southeast-1"
    )


@pytest.fixture(scope="session")
def rag_pipeline_message() -> RAGPipelineMessage:
    yield RAGPipelineMessage(
        agent="dad32f1794b94153a2fd9997929a4280",
        knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
        knowledge_bases=[],
        pipeline=RAGConfig(),
        results=[],
        supported_pipelines=[{}])


@pytest.fixture(scope="session")
def source_result() -> SourceResult:
    yield SourceResult(
        key="tests/examplecsv.csv"
    )


@pytest.fixture(scope="session")
def bucket_configs() -> tuple:
    private_bucket_name = "private_bucket"
    cloudfront_bucket_name = "cloudfront_bucket"
    test_files_dir = "./test_files"
    return private_bucket_name, cloudfront_bucket_name, test_files_dir


@pytest.fixture(scope="session")
def mock_aws_infra(bucket_configs) -> boto3.Session:
    with mock_aws():
        private_bucket_name, cloudfront_bucket_name, test_files_dir = bucket_configs
        REGION_NAME = "ap-southeast-1"
        session = boto3.Session(
            aws_access_key_id="FAKE_ACCESS_KEY_ID",
            aws_secret_access_key="FAKE_SECRET_ACCESS_KEY",
            region_name=REGION_NAME
        )

        config = {"LocationConstraint": REGION_NAME}
        # create client for s3 and sqs
        s3 = session.client("s3")
        sqs = session.client("sqs")
        # creates private bucket
        s3.create_bucket(Bucket=private_bucket_name,
                         CreateBucketConfiguration=config)
        # creates cloudfront bucket
        s3.create_bucket(Bucket=cloudfront_bucket_name,
                         CreateBucketConfiguration=config)
        # creates all files in cloudfront bucket
        for file_dir in os.listdir(test_files_dir):
            with open(f"{test_files_dir}/{file_dir}", mode="rb") as test_file:
                # uploads to cloudfront
                s3.upload_fileobj(
                    test_file, cloudfront_bucket_name, f"tests/{file_dir}")
            with open(f"{test_files_dir}/{file_dir}", mode="rb") as test_file:
                # uploads to private
                s3.upload_fileobj(
                    test_file, private_bucket_name, f"tests/{file_dir}")
        # initialises status queue
        os.environ["PROJECT_RAG_STATUS__URL"] = sqs.create_queue(QueueName="STATUS")[
            "QueueUrl"]

        file_types = ("PPTX", "DOCX", "CSV", "XLSX", "TXT", "PDF", "HTML")
        # initialise parser queues
        for name in file_types:
            url = sqs.create_queue(QueueName=name)["QueueUrl"]
            environ_name = f"PROJECT_RAG_PARSE__{name}__URL"
            os.environ[environ_name] = url

        chunking_types = ("FIXED", "DATAFRAME", "SEMANTIC")
        # initialise chunking queues
        for name in chunking_types:
            url = sqs.create_queue(QueueName=name)["QueueUrl"]
            environ_name = f"PROJECT_RAG_CHUNK_{name}__URL"
            os.environ[environ_name] = url

        # initialise storing queue
        os.environ["PROJECT_RAG_STORE__URL"] = sqs.create_queue(QueueName="STORE")[
            "QueueUrl"]

        yield session
    del os.environ["PROJECT_RAG_STORE__URL"]

    # delete all environ variables
    for name in file_types:
        environ_name = f"PROJECT_RAG_PARSE__{name}__URL"
        del os.environ[environ_name]

    for name in chunking_types:
        environ_name = f"PROJECT_RAG_CHUNK_{name}__URL"
        del os.environ[environ_name]
    del session
