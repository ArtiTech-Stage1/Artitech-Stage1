# 🎨 Artwork Retrieval and Recommendation System

AI-based intelligent artwork retrieval and recommendation system supporting multi-modal retrieval, personalized recommendations, and user interaction learning.

## 🏗️ System Architecture

```
User Query → Coarse Ranking Module → Fine Ranking Module → Diversity Filtering → Recommendation Results
    ↓         ↓         ↓          ↓         ↓
Query Understanding  Candidate Recall  Personalized Ranking  Deduplication Filtering  Batch Return
```

### Core Components

1. **Data Import Module** (`data_importer.py`) - CSV data import and preprocessing
2. **Tag Extractor** (`tag_extractor.py`) - Automatic extraction of color, style, theme, and emotion tags
3. **Embedding Service** (`embedding_service.py`) - Text vectorization and similarity calculation
4. **Retrieval Engine** (`retrieval_engine.py`) - Two-stage retrieval with coarse + fine ranking
5. **Recommendation Service** (`service.py`) - Business logic and data access
6. **API Routes** (`routes.py`) - RESTful API interfaces

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install sentence-transformers pandas numpy

# Ensure PostgreSQL database is running
# Ensure database tables are created (run schema.sql)
```

### 2. Data Import

```bash
# Navigate to artwork_retrieval directory
cd backend/artwork_retrieval

# Test import (first 100 records)
python import_csv_data.py test

# Check database status
python import_csv_data.py status

# Full import of all data
python import_csv_data.py full
```

### 3. Start Service

```bash
# Start backend service
cd backend
python main.py
```

### 4. API Testing

```bash
# Get recommendations
curl -X POST "http://localhost:8000/api/artworks/recommend" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "peaceful landscape painting",
    "mood": "calm",
    "preferred_colors": ["blue", "green"],
    "limit": 10
  }'

# Search artworks
curl "http://localhost:8000/api/artworks/search?query=monet&limit=5"

# Get artwork details
curl "http://localhost:8000/api/artworks/artwork/{artwork_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 Database Design

### Core Table Structure

#### artworks table
```sql
- id: UUID (primary key)
- object_id: Artwork unique identifier
- title: Title
- artist_display_name: Artist
- culture: Cultural background
- period: Period
- general_text_description: Description
- color_tags: Color tag array
- style_tags: Style tag array
- theme_tags: Theme tag array
- emotion_tags: Emotion tag array
- popularity_score: Popularity score
- quality_score: Quality score
```

#### artwork_embeddings table
```sql
- artwork_id: Associated artwork ID
- embedding_type: Vector type (title/description/combined)
- embedding_vector: Vector data (JSON format)
- model_name: Model name
```

#### artwork_user_interactions table
```sql
- user_id: User ID
- artwork_id: Artwork ID
- interaction_type: Interaction type (view/like/dislike/save/share)
- interaction_score: Interaction score
- context: Context information
```

## 🔍 Detailed Retrieval Algorithm

### Coarse Ranking Stage

1. **Text Retrieval**
   - Use PostgreSQL full-text search
   - Based on title, description, artist name
   - Support multi-language and fuzzy matching

2. **Vector Retrieval**
   - Use Sentence-BERT to generate query vectors
   - Calculate cosine similarity with artwork vectors
   - Support semantic understanding and cross-language retrieval

3. **Tag Matching**
   - Based on user preferences and query tags
   - Support color, style, theme, emotion dimensions
   - Use array intersection operations for fast matching

### Fine Ranking Stage

Comprehensive scoring formula:
```
Final_Score = α × Preference_Score + β × Mood_Score + γ × Popularity_Score + δ × Quality_Score + ε × Vector_Score
```

Where:
- **Preference_Score**: User preference matching degree
- **Mood_Score**: Mood matching degree  
- **Popularity_Score**: Artwork popularity
- **Quality_Score**: Artwork quality
- **Vector_Score**: Semantic similarity

### Diversity Filtering

- **Artist Diversity**: Limit number of works by same artist
- **Style Diversity**: Avoid over-concentration in single style
- **Theme Diversity**: Ensure theme richness

## 🎯 Recommendation Strategy

### Batch Recommendation Mechanism

1. **First Batch** (3 items): High-quality recommendations after fine ranking
2. **Second Batch** (3 items): Medium-quality recommendations after fine ranking
3. **Subsequent Batches**: Coarse ranking results, ensuring sufficient quantity

### Personalization Strategy

1. **Explicit Preferences**: User-set color, style, theme preferences
2. **Implicit Preferences**: Learning based on user interaction history
3. **Context Awareness**: Adjust recommendations based on current mood state
4. **Collaborative Filtering**: Based on similar users' preferences

## 📈 Performance Optimization

### Caching Strategy

- **Recommendation Cache**: 24-hour TTL, generate cache keys based on query features
- **Vector Cache**: Memory cache for common vector calculation results
- **User Profile Cache**: Cache user preferences and interaction history

### Index Optimization

```sql
-- Text search index
CREATE INDEX idx_artworks_fulltext ON artworks USING gin(to_tsvector('english', title || ' ' || description));

-- Tag indexes
CREATE INDEX idx_artworks_color_tags ON artworks USING gin(color_tags);
CREATE INDEX idx_artworks_style_tags ON artworks USING gin(style_tags);

-- Score indexes
CREATE INDEX idx_artworks_popularity ON artworks(popularity_score DESC);
```

### Batch Processing Optimization

- **Batch Import**: Avoid memory overflow
- **Asynchronous Processing**: Background vector and tag generation
- **Incremental Updates**: Support incremental data import

## 🔧 Configuration Parameters

### RetrievalConfig Configuration

```python
config = RetrievalConfig(
    # Coarse ranking configuration
    coarse_ranking_limit=100,        # Coarse ranking candidate count
    text_search_weight=0.3,          # Text search weight
    vector_search_weight=0.7,        # Vector search weight
    
    # Fine ranking configuration  
    fine_ranking_limit=20,           # Fine ranking candidate count
    user_preference_weight=0.4,      # User preference weight
    mood_weight=0.3,                 # Mood weight
    popularity_weight=0.2,           # Popularity weight
    
    # Diversity configuration
    max_same_artist=2,               # Maximum same artist count
    max_same_style=3,                # Maximum same style count
    
    # Cache configuration
    cache_ttl_hours=24,              # Cache expiration time
    enable_cache=True                # Enable cache
)
```

## 📝 API Interface Documentation

### Recommendation Interface

**POST** `/api/artworks/recommend`

Request body:
```json
{
  "query": "peaceful landscape painting",
  "mood": "calm", 
  "preferred_colors": ["blue", "green"],
  "preferred_styles": ["impressionism"],
  "preferred_themes": ["landscape"],
  "limit": 10,
  "offset": 0
}
```

Response:
```json
{
  "artworks": [...],
  "scores": [0.95, 0.87, 0.82, ...],
  "total_count": 1250,
  "has_more": true,
  "cache_used": false
}
```

### Search Interface

**GET** `/api/artworks/search`

Parameters:
- `query`: Search keywords
- `department`: Department filter
- `culture`: Culture filter
- `artist`: Artist filter
- `sort_by`: Sort method (relevance/popularity/date/title)
- `limit`: Return count
- `offset`: Offset

### Interaction Recording Interface

**POST** `/api/artworks/artwork/{artwork_id}/interaction`

Request body:
```json
{
  "interaction_type": "like",
  "interaction_score": 1.0
}
```

## 🧪 Testing and Validation

### Unit Testing

```bash
# Run tests
python -m pytest artwork_retrieval/tests/

# Test coverage
python -m pytest --cov=artwork_retrieval
```

### Performance Testing

```bash
# Import performance testing
python import_csv_data.py test

# Retrieval performance testing
python -m artwork_retrieval.tests.test_performance
```

### Recommendation Quality Assessment

- **Accuracy**: User click-through rate
- **Diversity**: Diversity metrics of recommendation results
- **Novelty**: Ability to recommend new artworks
- **Coverage**: Coverage of artwork database

## 🔮 Future Expansion

### Planned Features

1. **Visual Feature Extraction**: Image-based similarity calculation
2. **Deep Learning Ranking**: Use neural networks to optimize ranking
3. **Real-time Personalization**: Adjust recommendations based on real-time behavior
4. **Multi-modal Fusion**: Combine text, image, audio features
5. **A/B Testing Framework**: Support online experiments for recommendation strategies

### Technical Upgrades

1. **Vector Database**: Migrate to professional vector database (Pinecone/Weaviate)
2. **Distributed Computing**: Support large-scale data processing
3. **GPU Acceleration**: Use GPU to accelerate vector calculations
4. **Stream Processing**: Real-time data updates and recommendations

## 🐛 Troubleshooting

### Common Issues

1. **Import Failure**
   - Check CSV file format and encoding
   - Confirm database connection is normal
   - View log file `artwork_import.log`

2. **Empty Recommendation Results**
   - Confirm data has been imported correctly
   - Check user preference settings
   - Lower similarity threshold

3. **Performance Issues**
   - Check database indexes
   - Adjust batch processing size
   - Enable caching mechanism

### Log Analysis

```bash
# View import logs
tail -f artwork_import.log

# View application logs
tail -f app.log | grep artwork
```

---

*This artwork retrieval and recommendation system provides a complete end-to-end solution, from data import to personalized recommendations, supporting intelligent retrieval and recommendation of large-scale artwork databases.*
