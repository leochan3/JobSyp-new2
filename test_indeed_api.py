#!/usr/bin/env python3
import requests
import json

# Test Indeed API with different limits
def test_indeed_api(limit=100):
    api_url = "https://apis.indeed.com/graphql"
    
    # Test query with company search
    query = f"""
    query GetCompanyJobData {{
        jobSearch(
        what: "company:Walmart"
        location: {{where: "usa", radius: 50, radiusUnit: MILES}}
        limit: {limit}
        sort: RELEVANCE
        ) {{
        pageInfo {{
            nextCursor
        }}
        results {{
            trackingKey
            job {{
            source {{
                name
            }}
            key
            title
            datePublished
            dateOnIndeed
            description {{
                html
            }}
            location {{
                countryName
                countryCode
                admin1Code
                city
                postalCode
                streetAddress
                formatted {{
                short
                long
                }}
            }}
            compensation {{
                estimated {{
                currencyCode
                baseSalary {{
                    unitOfWork
                    range {{
                    ... on Range {{
                        min
                        max
                    }}
                    }}
                }}
                }}
                baseSalary {{
                unitOfWork
                range {{
                    ... on Range {{
                    min
                    max
                    }}
                }}
                }}
                currencyCode
            }}
            attributes {{
                key
                label
            }}
            employer {{
                relativeCompanyPageUrl
                name
                dossier {{
                    employerDetails {{
                    addresses
                    industry
                    employeesLocalizedLabel
                    revenueLocalizedLabel
                    briefDescription
                    ceoName
                    ceoPhotoUrl
                    }}
                    images {{
                        headerImageUrl
                        squareLogoUrl
                    }}
                    links {{
                    corporateWebsite
                }}
                }}
            }}
            recruit {{
                viewJobUrl
                detailedSalary
                workSchedule
            }}
            }}
        }}
        }}
    }}
    """
    
    headers = {
        "authority": "apis.indeed.com",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "indeed-co": "US",
        "origin": "https://www.indeed.com",
        "referer": "https://www.indeed.com/",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }
    
    payload = {"query": query}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"Response keys: {list(data.keys()) if data else 'None'}")
            
            if data and "data" in data:
                job_search = data["data"].get("jobSearch")
                if job_search:
                    results = job_search.get("results", [])
                    print(f"Number of jobs returned: {len(results)}")
                    print(f"Has nextCursor: {'pageInfo' in job_search and 'nextCursor' in job_search['pageInfo']}")
                else:
                    print("No jobSearch in response")
                    print(f"Data structure: {data['data']}")
            else:
                print("No 'data' in response")
                print(f"Full response: {data}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing Indeed API with limit 100:")
    test_indeed_api(100)
    
    print("\n" + "="*50 + "\n")
    
    print("Testing Indeed API with limit 200:")
    test_indeed_api(200) 