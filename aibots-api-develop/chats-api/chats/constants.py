from __future__ import annotations

__all__ = ("DEFAULT_APP_MESSAGES",)

DEFAULT_APP_MESSAGES: dict[str, dict[str, str]] = {
    "chats": {
        "api_chats_chat_not_found_msg": "Chat does not exist",
        "api_chats_chat_no_updates_msg": "No updates were made to Chat",
        "api_chats_chat_create_msg": "Creating Chat",
        "api_chats_chat_create_error_msg": "Error creating Chat",
        "api_chats_chat_delete_duplicate_id_msg": "Duplicate IDs found in deletion list",  # noqa: E501
        "api_chats_chat_delete_missing_error_msg": "Error deleting Chat Item(s), some chats do not exist",  # noqa: E501
        "api_chats_chat_update_fmt": "Updating Chat {}",
        "api_chats_chat_update_error_fmt": "Error updating Chat {}",
        "api_chats_chat_update_error_msg": "Error updating Chat",
        "api_chats_chat_delete_fmt": "Deleting Chat(s) {}",
        "api_chats_send_email_fmt": "Sending email of chat {} to {}",
        "api_chats_invalid_params_msg": "Invalid LLM parameters provided",
        "api_chats_chat_message_unrecognised_stream_error_msg": "Unrecognised stream data received",  # noqa: E501
        "api_chats_chat_message_create_msg": "Creating Chat Message",
        "api_chats_chat_message_rag_query_error_fmt": "Error {}.{} occurred when querying Agent's {} RAG pipeline {}",  # noqa: E501
        "api_chats_chat_message_update_fmt": "Updating Chat Message {}",
        "api_chats_chat_message_update_error_fmt": "Error updating Chat Message {}",  # noqa: E501
        "api_chats_chat_message_create_error_msg": "Error creating Chat Message",  # noqa: E501
        "api_chats_chat_message_update_error_msg": "Error updating Chat Message",  # noqa: E501
        "api_chats_chat_message_not_found_msg": "Chat Message(s) does not exist",  # noqa: E501
        "api_chats_chat_message_no_updates_msg": "No updates were made to Chat Message",  # noqa: E501
        "api_chats_chat_message_delete_fmt": "Deleting Chat Message(s) {}",
        "api_chats_chat_message_update_chat_fmt": "Removing Chat Messages {} from Chat {}",
        "api_chats_chat_message_unrecognised_stream_msg": "Unrecognised stream content type",  # noqa: E501
        "api_chats_agent_not_found_msg": "Agent(s) does not exist",
        "api_chats_agent_chat_config_not_found_msg": "Agent Chat Config is missing",  # noqa: E501
    },
    "rag": {
        "api_rag_pipeline_not_found_error_msg": "RAG Pipeline does not exist",
        "api_rag_cannot_rag_on_playground_bot_error_msg": "Cannot perform RAG on Playground Bot",  # noqa: E501
        "api_rag_update_agent_error_msg": "Error updating Agent",  # noqa: E501
        "api_rag_update_knowledge_base_error_msg": "Error updating Knowledge Bases",  # noqa: E501
        "api_rag_update_pipeline_error_msg": "Error updating RAG pipeline",  # noqa: E501
        "api_rag_perform_rag_on_invalid_knowledge_base_error_msg": "Attempting to perform rag on a knowledge base not associated with the Bot",  # noqa: E501
        "api_rag_perform_rag_on_invalid_pipeline_configuration_error_msg": "Attempting to perform rag on a invalid pipeline configuration",  # noqa: E501
        "api_rag_agent_no_rag_config_error_msg": "Bot was not configured with a RAG pipeline",  # noqa: E501
        "api_rag_generate_pipeline_fmt": "Triggering RAG pipeline {} of Agent {} for Knowledge Base {}",  # noqa: E501
        "api_rag_generate_pipeline_success_fmt": "Successfully triggered RAG pipeline {} of Agent {} for Knowledge Bases {}",  # noqa: E501
    },
    "schemas": {
        "api_schemas_ai_model_not_found_error_msg": "AI Model not found"
    },
}
