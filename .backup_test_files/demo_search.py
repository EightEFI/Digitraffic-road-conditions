#!/usr/bin/env python3
"""Demo script showing the road section search functionality."""

# Inline the mock data and search logic
MOCK_ROAD_SECTIONS = [
    {
        "id": "E18_0_50",
        "name": "E18: Tietokatu",
        "road": "E18",
        "location": "Tietokatu",
        "km": "0.0-50.0",
        "description": "Helsinki - Kilo area"
    },
    {
        "id": "E18_50_100",
        "name": "E18: Kehä III - Espoo boundary",
        "road": "E18",
        "location": "Kehä III - Espoo boundary",
        "km": "50.0-100.0",
        "description": "Espoo area"
    },
    {
        "id": "E75_0_40",
        "name": "E75: Hakamäentie",
        "road": "E75",
        "location": "Hakamäentie",
        "km": "0.0-40.0",
        "description": "Helsinki - Turku road start"
    },
    {
        "id": "E75_40_100",
        "name": "E75: Lohja area",
        "road": "E75",
        "location": "Lohja",
        "km": "40.0-100.0",
        "description": "Lohja - Turku area"
    },
    {
        "id": "VT1_0_50",
        "name": "VT1: Hämeentie",
        "road": "VT1",
        "location": "Hämeentie",
        "km": "0.0-50.0",
        "description": "Helsinki - Tampere start"
    },
    {
        "id": "VT1_50_120",
        "name": "VT1: Karviainen area",
        "road": "VT1",
        "location": "Karviainen",
        "km": "50.0-120.0",
        "description": "Inland towards Tampere"
    },
    {
        "id": "VT3_0_45",
        "name": "VT3: Länsimetro area",
        "road": "VT3",
        "location": "Länsimetro",
        "km": "0.0-45.0",
        "description": "Helsinki - Turku alternative route start"
    },
    {
        "id": "VT4_0_50",
        "name": "VT4: Tuusula area",
        "road": "VT4",
        "location": "Tuusula",
        "km": "0.0-50.0",
        "description": "Helsinki - Oulu start"
    },
    {
        "id": "VT4_50_130",
        "name": "VT4: Perämerentie",
        "road": "VT4",
        "location": "Perämerentie",
        "km": "50.0-130.0",
        "description": "Oulu direction - central area"
    },
    {
        "id": "VT4_130_200",
        "name": "VT4: Oulu area",
        "road": "VT4",
        "location": "Oulu",
        "km": "130.0-200.0",
        "description": "Oulu region"
    },
    {
        "id": "ST101_0_30",
        "name": "ST101: Itäväylä",
        "road": "ST101",
        "location": "Itäväylä",
        "km": "0.0-30.0",
        "description": "Helsinki east ring road"
    },
    {
        "id": "ST105_0_25",
        "name": "ST105: Westbound area",
        "road": "ST105",
        "location": "Westbound",
        "km": "0.0-25.0",
        "description": "Helsinki west area"
    },
]


def search_road_sections(query):
    """Search for road sections by name, road number, or location."""
    query_lower = query.lower().strip()
    
    if not query_lower:
        return []
    
    matching = []
    for section in MOCK_ROAD_SECTIONS:
        if (query_lower in section.get("road", "").lower() or
            query_lower in section.get("location", "").lower() or
            query_lower in section.get("name", "").lower() or
            query_lower in section.get("description", "").lower()):
            matching.append(section)
    
    return matching


def demo():
    """Demonstrate the search functionality."""
    print("=" * 75)
    print("DigiTraffic - Search functionality demo")
    print("=" * 75)
    
    # Example search queries
    test_queries = [
        "E18",
        "VT4",
        "Perämerentie",
        "Hämeentie",
        "Helsinki",
        "Tampere",
        "area",
        "st",
    ]
    
    for query in test_queries:
        print(f"\n📍 Searching for: '{query}'")
        print("-" * 75)
        
        results = search_road_sections(query)
        
        if results:
            print(f"✓ Found {len(results)} result(s):\n")
            for i, section in enumerate(results, 1):
                road = section.get("road", "N/A")
                name = section.get("name", "N/A")
                location = section.get("location", "N/A")
                km = section.get("km", "N/A")
                description = section.get("description", "N/A")
                section_id = section.get("id", "N/A")
                
                print(f"  {i}. {name}")
                print(f"     Road: {road}")
                print(f"     Location: {location}")
                print(f"     KM: {km}")
                print(f"     Description: {description}")
                print(f"     ID: {section_id}")
                print()
        else:
            print("✗ No results found\n")
    
    print("\n" + "=" * 75)
    print("ALL AVAILABLE ROAD SECTIONS (Total: {})".format(len(MOCK_ROAD_SECTIONS)))
    print("=" * 75)
    
    for i, section in enumerate(MOCK_ROAD_SECTIONS, 1):
        print(f"{i:2d}. {section.get('name'):35s} | {section.get('road'):5s} | {section.get('location'):20s} [{section.get('km')}]")


if __name__ == "__main__":
    demo()
