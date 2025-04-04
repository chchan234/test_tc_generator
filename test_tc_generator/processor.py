from typing import List, Dict, Any
import random
import os
import google.generativeai as genai
from openai import OpenAI
from langchain_core.documents import Document

# Configure API clients based on keys
def configure_api_clients(model_option, api_keys):
    if model_option == "Google Gemini" and "gemini" in api_keys:
        genai.configure(api_key=api_keys["gemini"])
        return "gemini"
    elif model_option == "OpenAI GPT-4 Turbo" and "openai" in api_keys:
        return OpenAI(api_key=api_keys["openai"])
    else:
        raise ValueError("API 키가 설정되지 않았습니다.")

# Function to filter unnecessary sentences using AI
def filter_unnecessary_sentences(sentences: List[Document], model_option: str, api_keys: Dict[str, str]) -> List[Document]:
    api_client = configure_api_clients(model_option, api_keys)
    
    filtered_sentences = []
    
    for sentence in sentences:
        content = sentence.page_content
        
        # Skip empty or very short content
        if not content or len(content.strip()) < 10:
            continue
        
        is_useful = _check_if_useful_for_testcase(content, model_option, api_client)
        
        if is_useful:
            filtered_sentences.append(sentence)
    
    return filtered_sentences

def _check_if_useful_for_testcase(content: str, model_option: str, api_client: Any) -> bool:
    prompt = f"""
    다음 문장이 게임 테스트케이스 생성에 유용한지 판단해주세요. 
    테스트케이스란 소프트웨어 기능을 검증하기 위한 특정 조건, 입력값, 예상 결과를 포함한 시나리오입니다.
    
    문장이 다음과 같은 내용을 포함한다면 유용합니다:
    - 기능 설명 (사용자가 할 수 있는 행동)
    - 게임 시스템 동작 방식
    - 게임 내 조건과 결과
    - 오류 상황과 예외 처리
    
    다음 문장은 유용합니까? 예/아니오로만 대답해주세요.
    
    문장: {content}
    """
    
    if model_option == "Google Gemini":
        gemini_model = genai.GenerativeModel('gemini-pro')
        response = gemini_model.generate_content(prompt)
        answer = response.text.strip().lower()
        return "예" in answer or "yes" in answer
    else:
        response = api_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "게임 테스트케이스 생성에 유용한 문장을 판별합니다."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip().lower()
        return "예" in answer or "yes" in answer

# Function to identify document structure (major/medium/minor categories)
def identify_document_structure(filtered_sentences: List[Document], model_option: str, api_keys: Dict[str, str]) -> Dict[str, Any]:
    api_client = configure_api_clients(model_option, api_keys)
    
    # Join all filtered sentences to get a complete document view
    full_text = "\n".join([s.page_content for s in filtered_sentences])
    
    # Prompt to identify document structure
    prompt = f"""
    다음 게임 기획서 내용을 분석해서 대분류/중분류/소분류 체계를 식별해주세요.
    이 분류체계는 테스트케이스를 구성하는 데 사용될 것입니다.
    
    예시 형식:
    {{
      "대분류": ["시스템", "게임플레이", "UI", "네트워크", ...],
      "중분류": {{
        "시스템": ["로그인", "회원가입", "캐릭터 생성", ...],
        "게임플레이": ["전투", "퀘스트", "인벤토리", ...],
        ...
      }},
      "소분류": {{
        "로그인": ["성공 케이스", "실패 케이스", "오류 메시지", ...],
        "전투": ["공격", "방어", "스킬 사용", ...],
        ...
      }}
    }}
    
    문서 내용:
    {full_text}
    
    JSON 형식으로만 응답해주세요.
    """
    
    if model_option == "Google Gemini":
        gemini_model = genai.GenerativeModel('gemini-pro')
        response = gemini_model.generate_content(prompt)
        
        try:
            # Extract JSON from the response
            import json
            from json import JSONDecodeError
            
            # Try to find and parse JSON content
            response_text = response.text
            
            # Find JSON structure in the response
            import re
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                structure_json = json_match.group(1)
                return json.loads(structure_json)
            else:
                # Fallback to default structure
                return create_default_structure()
        except Exception as e:
            print(f"Error parsing document structure: {e}")
            return create_default_structure()
    else:
        try:
            response = api_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "게임 기획서의 구조를 분석하여 대분류/중분류/소분류를 JSON 형식으로 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            structure_text = response.choices[0].message.content
            return json.loads(structure_text)
        except Exception as e:
            print(f"Error getting document structure from OpenAI: {e}")
            return create_default_structure()

def create_default_structure():
    # Default structure when AI fails to identify document structure
    return {
        "대분류": ["시스템", "게임플레이", "UI", "기타"],
        "중분류": {
            "시스템": ["로그인", "설정", "계정"],
            "게임플레이": ["전투", "퀘스트", "캐릭터"],
            "UI": ["메뉴", "HUD", "인벤토리"],
            "기타": ["성능", "호환성"]
        },
        "소분류": {
            "로그인": ["성공", "실패", "오류"],
            "전투": ["공격", "방어", "스킬"],
            "메뉴": ["진입", "이동", "종료"],
            "성능": ["로딩", "프레임레이트"]
        }
    }

# Function to generate testcases from filtered sentences
def generate_testcases(filtered_sentences: List[Document], doc_structure: Dict[str, Any], model_option: str, api_keys: Dict[str, str]) -> List[Dict[str, Any]]:
    api_client = configure_api_clients(model_option, api_keys)
    
    testcases = []
    
    # Process sentences in batches to avoid token limits
    batch_size = 5
    for i in range(0, len(filtered_sentences), batch_size):
        batch = filtered_sentences[i:i+batch_size]
        batch_text = "\n".join([s.page_content for s in batch])
        
        # Format structure for the prompt
        structure_text = f"""
        대분류 옵션: {", ".join(doc_structure["대분류"])}
        
        중분류 예시:
        {", ".join([f"{major}: {', '.join(items)}" for major, items in doc_structure["중분류"].items()][:3])}
        
        소분류 예시:
        {", ".join([f"{medium}: {', '.join(items)}" for medium, items in doc_structure["소분류"].items()][:3])}
        """
        
        prompt = f"""
        다음 게임 기획서 내용을 바탕으로 테스트케이스를 생성해주세요.
        
        문서 구조:
        {structure_text}
        
        테스트케이스 양식:
        {{
            "대분류": "대분류명",
            "중분류": "중분류명",
            "소분류": "소분류명",
            "구분": "정상/예외/경계", 
            "테스트 내용": "테스트할 기능이나 동작의 요약",
            "테스트 조건": "테스트를 수행하기 위한 전제 조건",
            "기대 결과": "테스트 성공 시 예상되는 결과",
            "비고": "추가 참고사항"
        }}
        
        분석할 기획서 내용:
        {batch_text}
        
        각 문장마다 관련 테스트케이스를 1-3개 생성해주세요.
        JSON 배열 형식으로 응답해주세요.
        """
        
        batch_testcases = []
        
        if model_option == "Google Gemini":
            gemini_model = genai.GenerativeModel('gemini-pro')
            response = gemini_model.generate_content(prompt)
            
            try:
                import json
                import re
                
                # Try to find and parse JSON content
                response_text = response.text
                
                # Find JSON array structure in the response
                json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    batch_testcases = json.loads(json_str)
                else:
                    # Fallback to create generic testcase
                    batch_testcases = [create_generic_testcase(s.page_content, doc_structure) for s in batch]
            except Exception as e:
                print(f"Error parsing testcases: {e}")
                batch_testcases = [create_generic_testcase(s.page_content, doc_structure) for s in batch]
        else:
            try:
                response = api_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "게임 기획서 내용으로부터 테스트케이스를 생성합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                import json
                result_text = response.choices[0].message.content
                
                # Find JSON array in the response
                import re
                json_match = re.search(r'(\[.*\])', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    batch_testcases = json.loads(json_str)
                else:
                    # Try to parse the entire response as a JSON object with a testcases property
                    try:
                        result_obj = json.loads(result_text)
                        if isinstance(result_obj, list):
                            batch_testcases = result_obj
                        elif "testcases" in result_obj:
                            batch_testcases = result_obj["testcases"]
                        else:
                            batch_testcases = [create_generic_testcase(s.page_content, doc_structure) for s in batch]
                    except:
                        batch_testcases = [create_generic_testcase(s.page_content, doc_structure) for s in batch]
                        
            except Exception as e:
                print(f"Error getting testcases from OpenAI: {e}")
                batch_testcases = [create_generic_testcase(s.page_content, doc_structure) for s in batch]
        
        testcases.extend(batch_testcases)
    
    return testcases

def create_generic_testcase(sentence, doc_structure):
    # Fallback function to create a generic testcase when AI fails
    major_categories = doc_structure["대분류"]
    major = random.choice(major_categories)
    
    medium_options = doc_structure["중분류"].get(major, ["일반"])
    medium = random.choice(medium_options)
    
    minor_options = doc_structure["소분류"].get(medium, ["기본"])
    minor = random.choice(minor_options)
    
    tc_types = ["정상", "예외", "경계"]
    
    return {
        "대분류": major,
        "중분류": medium,
        "소분류": minor,
        "구분": random.choice(tc_types),
        "테스트 내용": f"다음 내용 검증: {sentence[:50]}...",
        "테스트 조건": "기본 게임 환경에서 테스트",
        "기대 결과": "기획서 내용과 일치하는 결과 확인",
        "비고": ""
    }

# Function to validate testcase quality
def validate_testcase_quality(testcases: List[Dict[str, Any]], model_option: str, api_keys: Dict[str, str]) -> List[Dict[str, Any]]:
    api_client = configure_api_clients(model_option, api_keys)
    
    validated_testcases = []
    
    for tc in testcases:
        # Format testcase for validation
        tc_text = f"""
        대분류: {tc['대분류']}
        중분류: {tc['중분류']}
        소분류: {tc['소분류']}
        구분: {tc['구분']}
        테스트 내용: {tc['테스트 내용']}
        테스트 조건: {tc['테스트 조건']}
        기대 결과: {tc['기대 결과']}
        비고: {tc['비고']}
        """
        
        prompt = f"""
        다음 테스트케이스의 품질을 평가해주세요. 각 항목별로 점수를 부여하고 총점을 계산해주세요.
        
        평가 항목:
        1. 정확성 (40점): 테스트 내용이 명확하고 테스트 조건과 기대 결과가 정확하게 매칭되는가?
        2. 명확성 (20점): 테스트케이스가 이해하기 쉽고 명확하게 작성되었는가?
        3. 중복성 (20점): 다른 테스트케이스와 중복되지 않고 고유한 가치를 제공하는가?
        4. 완전성 (20점): 테스트케이스가 필요한 모든 정보를 포함하고 있는가?
        
        테스트케이스:
        {tc_text}
        
        각 항목의 점수와 총점(100점 만점)만 JSON 형식으로 응답해주세요:
        {{
            "정확성": 점수,
            "명확성": 점수,
            "중복성": 점수,
            "완전성": 점수,
            "총점": 총합점수
        }}
        """
        
        score_data = {"정확성": 30, "명확성": 15, "중복성": 15, "완전성": 15, "총점": 75}  # Default scores
        
        if model_option == "Google Gemini":
            gemini_model = genai.GenerativeModel('gemini-pro')
            response = gemini_model.generate_content(prompt)
            
            try:
                import json
                import re
                
                # Find JSON object in the response
                response_text = response.text
                json_match = re.search(r'({.*})', response_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    score_data = json.loads(json_str)
                    
                    # Verify total score
                    total = sum([
                        score_data.get("정확성", 0),
                        score_data.get("명확성", 0),
                        score_data.get("중복성", 0),
                        score_data.get("완전성", 0)
                    ])
                    
                    score_data["총점"] = total
            except Exception as e:
                print(f"Error parsing quality scores: {e}")
        else:
            try:
                response = api_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "테스트케이스의 품질을 평가합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                import json
                score_text = response.choices[0].message.content
                score_data = json.loads(score_text)
                
                # Verify total score
                total = sum([
                    score_data.get("정확성", 0),
                    score_data.get("명확성", 0),
                    score_data.get("중복성", 0),
                    score_data.get("완전성", 0)
                ])
                
                score_data["총점"] = total
                
            except Exception as e:
                print(f"Error getting quality scores from OpenAI: {e}")
        
        # Add score to the testcase
        tc["점수"] = score_data["총점"]
        validated_testcases.append(tc)
    
    return validated_testcases
