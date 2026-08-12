/** Chat client types for collection-scoped RAG UI. */

export type ChatSession = {
  id: string;
  collection_id: string;
  title: string | null;
  created_at: string;
  last_message_at: string | null;
};

export type ChatTurn = {
  id: string;
  role: string;
  content: string;
  cited_chunk_ids: string[];
  cited_documents: string[];
  created_at: string;
};

export type ChatSessionDetail = ChatSession & {
  turns: ChatTurn[];
  rolling_summary: string | null;
};

export type ChatCitation = {
  chunk_id: string;
  document_id: string;
  text: string | null;
  page_numbers: number[] | null;
  section_path: string[] | null;
};

export type ChatStreamCitation = {
  chunk_id: string;
  start: number;
  end: number;
};

export type ChatStreamDone = {
  turn_id: string | null;
  insufficient: boolean;
  session_id: string;
  status?: string | null;
};

export type ChatStreamEvent =
  | { type: "token"; delta: string }
  | { type: "citation"; citation: ChatStreamCitation }
  | { type: "usage"; prompt_tokens: number; completion_tokens: number }
  | { type: "done"; done: ChatStreamDone };
