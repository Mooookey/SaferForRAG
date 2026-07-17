const axios = require("axios");

const base_url = process.env.API_BASE_URL || "http://127.0.0.1:8001/api/v1";
const scan_text = "我的身份证号是110101199003074493";
const input_text = "hello world";
const output_text = "hello world";
const detection_profile = "default";
const transformation_profile = "placeholder";

async function main() {
  const client = axios.create({
    baseURL: base_url,
    timeout: 120000,
  });

  console.log("测试API: health");
  const health = await client.get("/health");
  console.log("health:", JSON.stringify(health.data, null, 2));
  console.log("--------------------------\n");

  console.log("测试API: scan");
  const scan = await client.post("/scan", {
    text: scan_text,
    profile: detection_profile,
  });
  console.log("scan:", JSON.stringify(scan.data, null, 2));
  console.log("--------------------------\n");

  console.log("测试API: anonymize");
  const anonymize = await client.post("/anonymize", {
    text: scan_text,
    transformation_profile,
    analyzer_results: scan.data.results,
  });
  console.log("anonymize:", JSON.stringify(anonymize.data, null, 2));
  console.log("--------------------------\n");

  console.log("测试API: deanonymize");
  const deanonymize = await client.post("/deanonymize", {
    text: anonymize.data.engine_result.text,
    engine_result: anonymize.data.engine_result,
  });
  console.log("deanonymize:", JSON.stringify(deanonymize.data, null, 2));
  console.log("--------------------------\n");

  console.log("测试API: check_input");
  const check_input = await client.post("/check_input", {
    text: input_text,
    profile: "default",
  });
  console.log("check_input:", JSON.stringify(check_input.data, null, 2));
  console.log("--------------------------\n");

  console.log("测试API: check_output");
  const check_output = await client.post("/check_input", {
    text: output_text,
    profile: "default",
  });
  console.log("checkoutnput:", JSON.stringify(check_output.data, null, 2));
  console.log("--------------------------\n");
}

main().catch((error) => {
  if (error.response) {
    console.error("api_error:", JSON.stringify(error.response.data, null, 2));
  } else {
    console.error("test_error:", error.message);
  }
  process.exit(1);
});
