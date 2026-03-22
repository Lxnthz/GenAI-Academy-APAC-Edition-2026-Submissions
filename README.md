# Track 3 - Build AI-Powered Applications Using AI-Ready Database Like AlloyDB

## Track Focus

This lab focuses on using AI-ready, fully managed database to build and modernise applications with built-in AI capabilites. Participant learn how to enable natural language-driven data interactions. The emphasis is on simplifying data access while improving performance and scalability.

## Hands-on Labs

**Use Model Context Protocols (MCP) Tools with ADK Agents**

Codelabs 1: [AlloyDB Quick Setup | Google Codelabs](./Markdowns/AlloyDB%20Quick%20Setup%20Lab.md)

Codelabs 2: [Building a Real-Tiem Surplus Engine with Gemini 3 Flash & AlloyDB | Google Codelabs](https://codelabs.developers.google.com/gemini-3-flash-on-alloydb-sustainability-app?hl=en#0)

## Overview

This lab teaches you how to build an AI agentic using ADK that connects to external tools through an MCP server. You'll create a tour guide agent that fetches animal data from a zoo MCP server and enriches responses using Wikipedia. The lab demonstrate hot to separate AI reasoning  from data and tool access using secure APIs.

## What you'll learn

How to deploy AlloyDB for PostgreSQL

- How to enable AlloyDB AI natural language.
- How to create and tune a configuration for AI natural language.

How to generate SQL queries and get results using natural language.

## Google Skills Lab (Optional)

Lab: [Configure Vector Search in AlloyDB](https://www.skills.google/focuses/119405?catalog_rank=%7B%22rank%22%3A6%2C%22num_filters%22%3A0%2C%22has_search%22%3Atrue%7D&parent=catalog&search_id=66805173)

In this lab, you learn how to:

- Configure AlloyDB database to support vector search.
- Create a table and load data in AlloyDB
- Generate and store text embeddings in AlloyDB
- Perform vector search in AlloyDB using text embeddings.

## Project Submission

### Problem Statement

Build a **small AI-enabled database feature** using **AlloyDB for PostgreSQL** that enables users to **query a custom dataset using natural language** and receive meaningful results.

The goal of this mini project is to demonstrate how **AI-ready databases can be applied to a specific data use case**, beyond a guided lab environment.

### What You Must Build

You must build **one database-centric capability** using AlloyDB that satisfies **all** of the following:

Build a simple software setup where:

1. **A dataset of your choice** (different from the lab's default dataset) is stored in AlloyDB.
2. **At least one table schema is modified or created by you**.
3. **AlloyDB AI natural language** is enabled for this dataset.
4. A **natural language query related to your dataset's context** is provided.
5. The system:
   - Converts the natural language input into an SQL query.
   - Executes the query against AlloyDB.
   - Returns relevant results from your dataset.

### Explicit Constraint (Prevent Lab Reuse)

- You **may use lab as reference**, but:
  - The dataset **must not be the default lab dataset**.
  - At least **one query must be your own**, not copied from the lab
- The use case must be **described in one sentence** (eg. "Querying sales data", "Exploring support tickets").
