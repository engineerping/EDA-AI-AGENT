# 突破大语言模型局限：RAG技术的核心流程与关键概念解读

## 一、什么是 RAG

如果 AI Model 是发动机，那么 AI Agent 就是自动驾驶汽车，而 RAG 就是行车时的参考地图。

RAG：Retrieval-Augmented Generation（检索-增强 生成）

它的核心思想是：
> "先从外部知识库检索相关内容，再让 LLM 基于这些内容生成回答。"
也就是说：
```text
RAG = 检索（Retrieval） + 生成（Generation）
```

---
## 二、为什么需要 RAG

因为大语言模型本身有几个问题：
1. 容易产生幻觉（Hallucination）；
2. 不知道企业私有数据；
3. 知识有截止日期；
4. 无法实时更新知识。

例如：
```text
"在公司如何申请年假？"
```
普通 GPT 不可能知道，因为这些数据没有训练进模型。所以：
> RAG 的目标就是让模型能够"临时查资料"，而不是把所有知识都训练进模型。

---
## 三、RAG 开发的核心流程细节

概括：
```text
1. 文档切片（Chunking）
 ↓
2. 向量化（Embedding）
 ↓
3. 将向量存入向量数据库（Vector Database）
 ↓
4. 用户输入（Prompt）
 ↓
5. 检索（Retrieval）
 ↓
6. 生成回答（Generation）
```

细节：
### 1. Chunking（文档切块）
因为 LLM 的 Context Window 有限，不能直接把整本书都输入进去。所以需要：
```text
长文档 → 切成小块（Chunk）
```
例如：每块 500 tokens，或按段落切分。Chunk 太小会丢上下文，Chunk 太大会降低检索精度。

### 2. Embedding（向量化）
Embedding 的本质是：
> "把文本转换成向量"

例如：
```text
"猫"
→ [0.12, -0.88, ...]
```
向量能够表达语义相似度，例如猫、狗、宠物在向量空间里会比较接近。

### 3. Vector Database（向量数据库）
Embedding 之后，需要把向量存起来。常见向量数据库包括：pgvector、Pinecone、Milvus、Weaviate、Chroma。

### 4. Prompt（用户输入）
对用户输入的问题做 embedding；【注意这里不同于对文档做 embedding】

### 5. Retrieval（检索）
用户提问后，系统会：去向量库搜索最相似的 chunk。
例如用户问"如何申请年假？"，系统会找到"员工年假制度"相关文档。

### 6. Generation（生成）
最后，系统会把用户问题 + 检索结果一起交给 LLM，告诉 LLM ：
```text
请根据以下资料回答：
……
```
这一步就是 **Generation**。

---
## 四、RAG 与 Fine-tuning 的区别

很多人会把 RAG 和 Fine-tuning 混淆。
**Fine-tuning** 是：
> "把知识训练进模型"
特点：成本高、更新慢、训练复杂。

**RAG** 是：
> "外挂知识库"
特点：实时更新、成本低、企业最常用、不需要重新训练模型。
所以：
> 现在大多数企业 AI 系统都优先使用 RAG。

---
## 五、RAG 的本质

RAG 本质上其实是：

> "搜索系统 + LLM"

真正决定效果的，往往不是模型，而是：
> **Retrieval（检索质量）**

因为：
```text
Garbage In → Garbage Out
```
检索错了，LLM 一定回答错。

---
## 六、RAG 面临的核心挑战

企业里真正难的是：

### 1. Chunking
怎么切文档。

### 2. Retrieval Accuracy
如何提高召回准确率。

### 3. Hallucination
即使有 RAG，模型依然可能胡说。

### 4. Context Window
上下文窗口有限，不能无限塞内容。

### 5. Latency
RAG 会增加 embedding、检索、rerank，因此延迟会增加。

---
## 七、企业级 RAG 常见优化

### 1. Hybrid Search
> 关键词搜索 + 向量搜索
结合使用，因为纯 embedding 有时不稳定。

### 2. Re-ranking
先召回 Top 20，再重新排序 Top 5。

### 3. Query Rewrite
自动改写用户问题。例如把"它怎么配置？"改写成"Spring AI pgvector 如何配置？"

### 4. Context Compression
因为 Context Window 有限，所以需要压缩上下文。

---
## 八、RAG 与 Agent 的关系

**ChatBot：**
```text
用户 → LLM
```

**RAG：**
```text → 用户 → Retrieval → LLM
```

**Agent：**
```text → 用户 → Planning → Tool Use → RAG → Memory → LLM
```

所以：
> **RAG 是 Agent 的知识系统。**

### RAG 中的两个阶段

```
索引阶段（Indexing）  —  只处理知识库文档，提前一次性完成
查询阶段（Query）     —  只处理用户提问，实时完成，不存储
```

|                | 知识库文档             | 用户提问     |
| -------------- | ----------------- | -------- |
| 时机             | 提前处理，存入 Vector DB | 实时处理，不存储 |
| 目的             | 检索的来源             | 检索的种子    |
| 是否存入 Vector DB | ✅ 是               | ❌ 否      |

**用户的提问也会经过 Embedding（向量化），但只是为了在向量库中搜索相似内容。** 

## 九、RAG 与 Memory 的区别

### Memory — Agent 的记忆系统
```
RAG    — 从外部知识库检索（例如企业文档、产品手册）
Memory — 从对话历史中检索（例如之前聊过的内容）
```

**Memory 的原理：** 把多轮对话的历史切片，向量化，存入 Memery 的 Vector DB。但要注意Memery 的 Vector DB，与 RAG 的 Vector DB是分开的。

#### Hermes Agent 的 的特色就是利用了 Memory 来存储对话历史。

(https://github.com/nousresearch/hermes-agent) 是一个开源 Agent 项目，其设计特点：

```
Brief Agent Memory：
  - 长期记忆 → Vector DB 检索（RAG 方式）
  - 短期记忆 → 直接存在上下文窗口中

当对话变长时，会自动将早期的重要信息压入 Vector DB，
需要时再检索回来——这就是 Memory 的典型实现。
```

---
## 十、Java 语言中的 RAG 开发工具

Spring AI 是 Spring 生态为 AI 应用开发打造的框架，RAG 是其核心场景之一。

### Spring AI 的核心抽象

```java
// Embedding 模型接口
public interface EmbeddingModel {
    EmbeddingResponse embed(Document text);
    EmbeddingResponse embed(List<String> texts);
}

// 向量存储接口
public interface VectorStore {
    void add(List<Document> documents);
    List<Document> similaritySearch(String query);
    List<Document> similaritySearch(SearchRequest request);
}

// 检索器接口
public interface Retriever<T> {
    List<T> retrieve(String query);
}
```

### 支持的向量数据库

| 向量库          | 依赖                         | 说明                             |
| ------------ | -------------------------- | ------------------------------ |
| **pgvector** | `spring-ai-pgvector-store` | PostgreSQL 扩展，最适合已有 PG 基础设施的企业 |
| **Milvus**   | `spring-ai-milvus-store`   | 分布式，生产级大规模向量检索                 |
| **Pinecone** | `spring-ai-pinecone-store` | 云服务，无需运维                       |
| **Redis**    | `spring-ai-redis-store`    | 利用 Redis 的向量搜索能力               |

### 开发代码示例

#### 1. 配置 Embedding 模型
```java
// application.yml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
    embedding:
      openai:
        options:
          model: text-embedding-3-small
```

```java
@Configuration
public class EmbeddingConfig {
    @Bean
    public OpenAiEmbeddingModel embeddingModel(OpenAiApi api) {
        return new OpenAiEmbeddingModel(api);
    }
}
```

#### 2. 配置 VectorStore（以 pgvector 为例）

```java
@Configuration
public class VectorStoreConfig {

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource dataSource) {
        return new JdbcTemplate(dataSource);
    }

    @Bean
    public PgVectorStore pgVectorStore(JdbcTemplate jdbcTemplate,
                                        EmbeddingModel embeddingModel) {
        return new PgVectorStore(jdbcTemplate, embeddingModel);
    }
}
```

#### 3. 文档切分与入库

```java
@Service
public class DocumentIngestionService {

    private final VectorStore vectorStore;
    private final TextSplitter textSplitter = new TokenTextSplitter(500, 50);

    public void ingestDocument(String content) {
        // 切分文档
        List<Document> chunks = textSplitter.split(content);
        // 存入向量库（自动做 embedding）
        vectorStore.add(chunks);
    }
}
```

#### 4. RAG 查询

```java
@Service
public class RagQueryService {

    private final VectorStore vectorStore;
    private final ChatModel chatModel;

    public String query(String userQuestion) {
        // 1. 检索相关文档
        List<Document> docs = vectorStore.similaritySearch(userQuestion, 5);
        // 2. 拼接 Prompt
        String context = docs.stream()
            .map(Document::getContent)
            .collect(Collectors.joining("\n"));
        String prompt = """
            请根据以下资料回答问题。

            资料：
            %s

            问题：%s
            """.formatted(context, userQuestion);
        // 3. 调用 LLM 生成
        return chatModel.call(prompt);
    }
}
```

#### 5. 使用 RAG Advisor（更高级用法）

```java
// RAG Advisor 封装了检索 + 生成的全流程
ChatClient chatClient = ChatClient.create(chatModel);

String response = chatClient.prompt()
    .advisors(new RetrieverAdvisor(vectorStore,
        new MyPromptTemplate("请根据以下资料回答：{context}\n问题：{question}")))
    .user(userQuestion)
    .call()
    .content();
```

推荐组合：
```
Spring Boot 项目：
  spring-ai-openai + spring-ai-pgvector-store
  → 最快上手，适合已有 Spring Boot 经验的团队

生产环境：
  spring-ai-openai + spring-ai-milvus-store
  → 分布式向量检索 + Spring 全套运维能力
```

---
## 十一、Python 语言中的 RAG 开发工具

Python 生态 RAG 开发有四个主流框架，各有侧重：

| 框架             | 核心定位                      | 适用场景              |
| -------------- | ----------------------- | ----------------- |
| **LlamaIndex** | 专精 RAG，API 最简洁，上手最快，纯 RAG 场景首选       | 文档问答、RAG 快速原型     |
| **LangChain**  | 通用抽象，生态最丰富，能做一切但需要自己组装            | 通用 LLM 应用、工具链集成   |
| **LangGraph**  | 在 LangChain 之上，构建有状态、多步骤的 Agent 决策流） | 多步骤、可循环 Agent 决策流 |
| **Haystack**   | 企业级 Pipeline 设计，内置评估与监控，适合生产环境    | 生产部署、批处理、内置评估与监控  |


### 技术选型

| 场景                         | 推荐方案                        |
| -------------------------- | --------------------------- |
| 文档问答 / RAG 快速原型            | **LlamaIndex**（首选）          |
| 复杂 Agent 流程（循环、分支、工具调用）    | **LangChain + LangGraph**   |
| 企业级生产部署 / 需要评估与监控          | **Haystack**                |
| 已有 LangChain 项目，需增强 RAG 能力 | LangChain + LlamaIndex 混用   |

### 代码示例

#### 1. LangChain — 标准 RAG 流程

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 切文档
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents(texts=[...], metadatas=[...])

# 2. 存向量
vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings(), persist_directory="./chroma_db")

# 3. 检索 + 生成
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
```

#### 2. LangGraph — Agent 决策流

LangGraph 专门用于构建**有状态、多步骤、可循环**的 Agent 流程，核心概念：

```
State            — 流程中的共享数据（对话历史、检索结果）
Node             — 流程中的一个步骤（检索、生成、判断）
Edge             — 节点之间的连接，决定下一步
Conditional Edge — 根据状态决定走哪条分支
```

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve_fn)
graph.add_node("generate", generate_fn)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)

app = graph.compile()
result = app.invoke({"messages": [HumanMessage(content="公司的年假制度是什么？")]})
```

#### 3. LlamaIndex — 简洁 RAG 首选

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings

Settings.embed_model = "local"

# 1. 加载文档
docs = SimpleDirectoryReader("./data").load_data()

# 2. 建索引
index = VectorStoreIndex.from_documents(docs, vector_store=ChromaVectorStore(...))

# 3. 查询
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("公司的年假制度是什么？")
```

### 常用向量数据库（Python 客户端）

| 向量库          | Python 客户端                        | 特点                     |
| ------------ | --------------------------------- | ---------------------- |
| **Chroma**   | `chromadb`                        | 轻量，本地优先，最适合 RAG 入门     |
| **FAISS**    | `faiss-cpu`                       | Facebook 开源，无需服务，高密度向量 |
| **Milvus**   | `pymilvus`                        | 大规模分布式，生产级             |
| **Pinecone** | `pinecone-client`                 | 云服务，无需运维               |
| **Qdrant**   | `qdrant-client`                   | Rust 实现，高性能，支持混合检索     |
| **pgvector** | `psycopg2` + `pgvector` extension | PostgreSQL 扩展，现有数据库直接用 |

### Embedding 模型

```python
# OpenAI 官方（需要 API Key）
from langchain_openai import OpenAIEmbeddings

# 本地开源模型（无需 API Key）
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
model = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# Ollama 本地模型
from langchain_community.embeddings import OllamaEmbeddings
model = OllamaEmbeddings(model="nomic-embed-text")
```

### 快速启动推荐组合

```
入门：LlamaIndex + Chroma + OpenAI Embedding
生产：LangChain/LlamaIndex + Milvus/Pinecone + BGE embedding
本地：LlamaIndex + FAISS + Ollama Embedding
```

---
## 十二、Spring AI vs Python 生态对比

| 维度     | Spring AI                                | LangChain / LlamaIndex               |
| ------ | ---------------------------------------- | ------------------------------------ |
| 语言     | Java / Kotlin                            | Python                               |
| 生态     | 企业级 Spring 生态                            | 学术 / 创业公司为主                          |
| 复杂度    | 中等，需要了解 Spring 生态                        | 较高，API 频繁变化                          |
| RAG 组件 | EmbeddingModel + VectorStore + Retriever | langchain-core + langchain-community |
| 多模型支持  | 统一抽象，支持 OpenAI / Anthropic / DeepSeek 等  | 通过 LiteLLM 或各自集成                     |
| 特点     | 类型安全，Spring 生态无缝集成                       | 社区活跃，工具链丰富                           |

---

## 十三、总结

```text
RAG 本质上是：
"搜索系统 + 大语言模型"。

它通过在生成回答之前先检索外部知识，
解决了 LLM 知识过时、无法访问私有数据以及幻觉的问题。

而企业级 RAG 最核心的竞争力，
其实是 Retrieval，也就是检索质量。
```
