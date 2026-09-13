# Fruitful Insights: A Big Data Pipeline for Nutritional Analysis with ML and AI Assistant

## Introduction

### 1.1 Project Overview
This project implements a complete big data pipeline using the Fruityvice API as the data source. The pipeline includes ETL (Extract, Transform, Load), Exploratory Data Analysis, Machine Learning, Tableau Visualization, and an AI-powered assistant powered by Groq's Llama 3 model.

### 1.2 Dataset Overview
The data comes from the Fruityvice API (https://www.fruityvice.com), which provides nutritional information for various fruits. Each record contains the fruit name, family, and nutritional values (calories, sugar, carbohydrates, protein, fat) per 100g.

**Key Statistics:**
- Total fruits: 48
- Number of families: 25

**The question I wanted to answer:**
*"Can we accurately predict the calorie content of fruits based on their nutritional composition, and can we make this data accessible through visualizations and an AI assistant?"*

---

## Setup

### 1. Create Virtual Environment
```
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create `.env` file:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=final_fruit_db
DB_USER=postgres
DB_PASSWORD=******
GROQ_API_KEY=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
```

### 4. Create PostgreSQL Tables
Run in pgAdmin:
```sql
CREATE TABLE raw_fruits (
    id SERIAL PRIMARY KEY,
    raw_data JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_endpoint VARCHAR(255)
);

CREATE TABLE clean_fruits (
    fruit_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    family VARCHAR(50),
    calories NUMERIC(10,2),
    sugar NUMERIC(10,2),
    carbohydrates NUMERIC(10,2),
    protein NUMERIC(10,2),
    fat NUMERIC(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Run ETL Pipeline
```
python src/etl_pipeline.py
```

## Run EDA & ML Models
```
jupyter notebook notebooks/eda_ml.ipynb
```

## Export CSV for Tableau
Run the export cell in `eda_ml.ipynb` to generate `data/fruit_dashboard_data.csv`.

## Start AI Assistant
```
python -c "from src.ai_assistant import interactive_chat; interactive_chat()"
```

## Run Tests
```
pytest src/tests/ -v
```

## Tableau Dashboard
**Link:** https://public.tableau.com/views/FruitNutrition/FruitNutritionDashboardETLMLVisualization?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link

---

## Data Dictionary

| Column | Type | Description |
|--------|------|-------------|
| `fruit_id` | INTEGER | Unique identifier |
| `name` | VARCHAR | Fruit name |
| `family` | VARCHAR | Botanical family |
| `calories` | NUMERIC | Calories per 100g |
| `sugar` | NUMERIC | Sugar in grams per 100g |
| `carbohydrates` | NUMERIC | Carbs in grams per 100g |
| `protein` | NUMERIC | Protein in grams per 100g |
| `fat` | NUMERIC | Fat in grams per 100g |

---

## Data Flow

```
Fruityvice API
    ↓
Extract (extract.py)
    ↓
Transform (transform.py)
    ↓
Load (load.py) → PostgreSQL (raw_fruits + clean_fruits)
    ↓
    ├── EDA & ML (notebooks/eda_ml.ipynb)
    ├── Tableau (CSV → Tableau Public)
    └── AI Assistant (ai_assistant.py + Groq API)
```