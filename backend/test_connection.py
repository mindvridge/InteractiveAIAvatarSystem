"""
간단한 연결 테스트 스크립트
Backend 서버가 정상적으로 실행되는지 확인
"""

import asyncio
import httpx


async def test_health():
    """헬스 체크 엔드포인트 테스트"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✅ Backend server is running!")
            else:
                print("❌ Backend server is not responding correctly")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("Make sure the backend server is running on http://localhost:8000")


async def test_root():
    """루트 엔드포인트 테스트"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/")
            print(f"\nRoot endpoint:")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")


if __name__ == "__main__":
    print("Testing backend connection...\n")
    asyncio.run(test_health())
    asyncio.run(test_root())
