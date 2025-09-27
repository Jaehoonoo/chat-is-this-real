import asyncio, json
from mock import agent_b

SAMPLE = {
  "claims": [
    {"claim": "The WHO declared COVID-19 a pandemic on March 11, 2020."},
    {"claim": "Mars has two moons named Phobos and Deimos."}
  ]
}

async def run():
    session = await agent_b.async_create_session(user_id="local")
    resp = await agent_b.async_invoke(session=session, user_query=json.dumps(SAMPLE))
    # With output_schema set, this should already be valid JSON per VerifyOutput
    print(json.dumps(json.loads(resp.text), indent=2))

if __name__ == "__main__":
    asyncio.run(run())
