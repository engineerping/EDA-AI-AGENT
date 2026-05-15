# RAG 面试速成稿（适合面试直接讲）

## 一、什么是 RAG

RAG 的全称是：

# Retrieval-Augmented Generation

中文一般翻译为：

# 检索增强生成

它的核心思想是：

> “先从外部知识库检索相关内容，再让 LLM 基于这些内容生成回答。”

也就是说：

```text
RAG = 检索（Retrieval） + 生成（Generation）
```

---

# 二、为什么需要 RAG

因为大语言模型本身有几个问题：

1. 知识有截止日期
2. 不知道企业私有数据
3. 容易产生幻觉（Hallucination）
4. 无法实时更新知识

例如：

```text
“公司 2025 年报销制度是什么？”
```

普通 GPT 不可能知道。

因为这些数据没有训练进模型。

所以：

# RAG 的目标就是让模型能够“临时查资料”。

而不是把所有知识都训练进模型。

---

# 三、RAG 的核心流程

标准 RAG 流程如下：

```text
用户问题
 ↓
Embedding（向量化）
 ↓
Vector Search（向量检索）
 ↓
找到相关文档
 ↓
拼接 Prompt
 ↓
LLM 生成回答
```

---

# 四、RAG 的几个核心概念

---

## 1. Chunking（文档切块）

因为 LLM 的 Context Window 有限，

不能直接把整本书都输入进去。

所以需要：

```text
长文档 → 切成小块（Chunk）
```

例如：

* 每块 500 tokens
* 或按段落切分

Chunk 太小会丢上下文，

Chunk 太大会降低检索精度。

---

## 2. Embedding（向量化）

Embedding 的本质是：

# “把文本转换成向量”

例如：

```text
“猫”
→ [0.12, -0.88, ...]
```

向量能够表达语义相似度。

例如：

```text
猫、狗、宠物
```

它们在向量空间里会比较接近。

---

## 3. Vector Database（向量数据库）

Embedding 之后，

需要把向量存起来。

常见向量数据库包括：

* pgvector
* Pinecone
* Milvus
* Weaviate
* Chroma

---

## 4. Retrieval（检索）

用户提问后：

系统会：

1. 对问题做 embedding
2. 去向量库搜索最相似的 chunk

例如：

用户问：

```text
“如何申请年假？”
```

系统会找到：

```text
“员工年假制度”
```

相关文档。

---

## 5. Generation（生成）

最后：

系统会把：

```text
用户问题 + 检索结果
```

一起交给 LLM。

例如：

```text
请根据以下资料回答：
……
```

这一步就是：

# Generation

---

# 五、RAG 与 Fine-tuning 的区别

很多人会把 RAG 和 Fine-tuning 混淆。

---

## Fine-tuning

是：

# “把知识训练进模型”

特点：

* 成本高
* 更新慢
* 训练复杂

---

## RAG

是：

# “外挂知识库”

特点：

* 实时更新
* 成本低
* 企业最常用
* 不需要重新训练模型

所以：

# 现在大多数企业 AI 系统都优先使用 RAG。

---

# 六、RAG 的本质

RAG 本质上其实是：

# “搜索系统 + LLM”

真正决定效果的，

往往不是模型，

而是：

# Retrieval（检索质量）

因为：

```text
Garbage In → Garbage Out
```

检索错了，

LLM 一定回答错。

---

# 七、RAG 面临的核心挑战

企业里真正难的是：

---

## 1. Chunking

怎么切文档。

---

## 2. Retrieval Accuracy

如何提高召回准确率。

---

## 3. Hallucination

即使有 RAG，

模型依然可能胡说。

---

## 4. Context Window

上下文窗口有限。

不能无限塞内容。

---

## 5. Latency

RAG 会增加：

* embedding
* 检索
* rerank

因此延迟会增加。

---

# 八、企业级 RAG 常见优化

---

## 1. Hybrid Search

即：

# 关键词搜索 + 向量搜索

结合使用。

因为纯 embedding 有时不稳定。

---

## 2. Re-ranking

先召回：

```text
Top 20
```

再重新排序：

```text
Top 5
```

---

## 3. Query Rewrite

自动改写用户问题。

例如：

```text
“它怎么配置？”
```

改写成：

```text
“Spring AI pgvector 如何配置？”
```

---

## 4. Context Compression

因为 Context Window 有限，

所以需要压缩上下文。

---

# 九、RAG 与 Agent 的关系

ChatBot：

```text
用户 → LLM
```

RAG：

```text
用户 → Retrieval → LLM
```

Agent：

```text
用户
 ↓
Planning
 ↓
Tool Use
 ↓
RAG
 ↓
Memory
 ↓
LLM
```

所以：

# RAG 是 Agent 的知识系统。

---

# 十、Spring AI 中的 RAG

[Spring AI 官方](https://spring.io/projects/spring-ai?utm_source=chatgpt.com)

Spring AI 已经内置：

* EmbeddingModel
* VectorStore
* Retriever
* RAG Advisor

支持：

* pgvector
* Redis
* Pinecone
* Milvus

因此：

# Java 企业开发现在也可以非常方便地做 RAG。

---

# 十一、最后一句总结（面试收尾）

如果面试官问：

# “RAG 的本质是什么？”

我会回答：

```text
RAG 本质上是：
“搜索系统 + 大语言模型”。

它通过在生成回答之前先检索外部知识，
解决了 LLM 知识过时、无法访问私有数据以及幻觉的问题。

而企业级 RAG 最核心的竞争力，
其实是 Retrieval，也就是检索质量。
```
