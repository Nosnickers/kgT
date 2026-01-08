import json
import re
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    name: str = Field(description="The name of the entity")
    type: str = Field(description="The type of the entity (Organization, Product, Material, Goal, Metric, Initiative, Location, etc.)")
    description: Optional[str] = Field(default="", description="A brief description of the entity")


class ExtractedRelationship(BaseModel):
    source: str = Field(description="The name of the source entity")
    target: str = Field(description="The name of the target entity")
    type: str = Field(description="The type of relationship (ACHIEVES, USES, REDUCES, CONTAINS, IMPLEMENTS, LOCATED_IN, etc.)")
    description: Optional[str] = Field(default="", description="A brief description of the relationship")


class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list, description="List of extracted entities")
    relationships: List[ExtractedRelationship] = Field(default_factory=list, description="List of extracted relationships")


class EntityExtractor:
    ENTITY_TYPES = [
        "Organization", "Product", "Material", "Goal", "Metric", 
        "Initiative", "Location", "Person", "Technology", "Program"
    ]
    
    RELATIONSHIP_TYPES = [
        "ACHIEVES", "USES", "REDUCES", "CONTAINS", "IMPLEMENTS", 
        "LOCATED_IN", "PARTNERS_WITH", "PRODUCES", "MEASURES", "TARGETS"
    ]

    def __init__(self, base_url: str, model: str, temperature: float = 0.1, num_ctx: int = 4096):
        self.llm = ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
            num_ctx=num_ctx
        )
        self.parser = JsonOutputParser(pydantic_object=ExtractionResult)

    def create_extraction_prompt(self) -> ChatPromptTemplate:
        system_prompt = """You are an expert knowledge graph builder specializing in extracting entities and relationships from environmental and business reports.

Your task is to extract entities and relationships from the given text and return them in a structured JSON format.

ENTITY TYPES (use only these):
- Organization: Companies, institutions, groups (e.g., Apple, suppliers, communities)
- Product: Products, devices, services (e.g., MacBook Air, iPhone 15, Apple Watch)
- Material: Materials, elements, substances (e.g., aluminum, cobalt, tungsten, lithium)
- Goal: Objectives, targets, commitments (e.g., Apple 2030, carbon neutrality)
- Metric: Measurements, statistics, percentages (e.g., emissions, recycled percentage, water usage)
- Initiative: Programs, projects, campaigns (e.g., Power for Impact, Grid Forecast)
- Location: Places, regions, countries (e.g., Nepal, Colombia, India, Brazil)
- Person: Individuals, roles (e.g., Lisa Jackson, VP)
- Technology: Technologies, methods, processes (e.g., renewable energy, recycling)
- Program: Structured programs or frameworks (e.g., Supplier Clean Water Program)

RELATIONSHIP TYPES (use only these):
- ACHIEVES: Organization → Goal (an organization achieves a goal)
- USES: Product → Material (a product uses a material)
- REDUCES: Initiative → Metric (an initiative reduces a metric)
- CONTAINS: Product → Material (a product contains a material)
- IMPLEMENTS: Organization → Initiative (an organization implements an initiative)
- LOCATED_IN: Initiative → Location (an initiative is located in a location)
- PARTNERS_WITH: Organization → Organization (organizations partner together)
- PRODUCES: Organization → Product (an organization produces a product)
- MEASURES: Metric → Goal (a metric measures progress toward a goal)
- TARGETS: Goal → Metric (a goal targets a specific metric)

EXTRACTION RULES:
1. Extract only entities that are explicitly mentioned in the text
2. Extract only relationships that are explicitly stated or strongly implied
3. Use exact names from the text when possible
4. Assign the most specific entity type from the allowed list
5. Assign the most appropriate relationship type from the allowed list
6. Include brief descriptions for entities and relationships when relevant
7. Do not hallucinate entities or relationships not present in the text
8. Return results in valid JSON format

OUTPUT FORMAT:
Return a JSON object with the following structure:
{
  "entities": [
    {
      "name": "entity_name",
      "type": "entity_type",
      "description": "brief description"
    }
  ],
  "relationships": [
    {
      "source": "source_entity_name",
      "target": "target_entity_name",
      "type": "relationship_type",
      "description": "brief description"
    }
  ]
}"""

        human_prompt = """Extract entities and relationships from the following text:

Text:
{text}

Return the extraction result in JSON format."""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

    def extract(self, text: str) -> ExtractionResult:
        prompt = self.create_extraction_prompt()
        
        formatted_prompt = prompt.format_messages(text=text)
        
        try:
            response = self.llm.invoke(formatted_prompt)
            content = response.content
            
            content = self.clean_json_response(content)
            
            result_data = json.loads(content)
            
            entities = [
                ExtractedEntity(**entity) for entity in result_data.get("entities", [])
            ]
            relationships = [
                ExtractedRelationship(**rel) for rel in result_data.get("relationships", [])
            ]
            
            return ExtractionResult(entities=entities, relationships=relationships)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response content: {content}")
            return ExtractionResult(entities=[], relationships=[])
        except Exception as e:
            print(f"Extraction error: {e}")
            return ExtractionResult(entities=[], relationships=[])

    def clean_json_response(self, content: str) -> str:
        content = content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        content = re.sub(r'^\s*[\{\[]', '', content)
        content = re.sub(r'[\}\]]\s*$', '', content)
        
        if not content.startswith('{'):
            content = '{' + content
        if not content.endswith('}'):
            content = content + '}'
        
        return content

    def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        results = []
        for text in texts:
            result = self.extract(text)
            results.append(result)
        return results

    def validate_extraction(self, result: ExtractionResult) -> bool:
        for entity in result.entities:
            if entity.type not in self.ENTITY_TYPES:
                print(f"Warning: Invalid entity type '{entity.type}' for entity '{entity.name}'")
                return False
        
        for rel in result.relationships:
            if rel.type not in self.RELATIONSHIP_TYPES:
                print(f"Warning: Invalid relationship type '{rel.type}' for relationship '{rel.source} -> {rel.target}'")
                return False
        
        return True

    def get_extraction_stats(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        total_entities = sum(len(result.entities) for result in results)
        total_relationships = sum(len(result.relationships) for result in results)
        
        entity_type_counts = {}
        relationship_type_counts = {}
        
        for result in results:
            for entity in result.entities:
                entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1
            
            for rel in result.relationships:
                relationship_type_counts[rel.type] = relationship_type_counts.get(rel.type, 0) + 1
        
        return {
            "total_chunks": len(results),
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "avg_entities_per_chunk": total_entities / len(results) if results else 0,
            "avg_relationships_per_chunk": total_relationships / len(results) if results else 0,
            "entity_type_distribution": entity_type_counts,
            "relationship_type_distribution": relationship_type_counts
        }
