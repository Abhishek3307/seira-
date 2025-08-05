// jest.config.js
module.exports = {
  // स्वचालित रूप से प्रत्येक टेस्ट के बीच मॉक कॉल और इंस्टेंस साफ़ करें
  clearMocks: true,

  // वह डायरेक्टरी जहाँ Jest को अपनी कवरेज फ़ाइलें आउटपुट करनी चाहिए
  coverageDirectory: "coverage",

  // रेगेक्स पैटर्न का एक ऐरे जिन्हें Jest को फ़ाइलें खोजते समय छोड़ देना चाहिए
  testPathIgnorePatterns: [
    "/node_modules/",
    "/venv/", // Python वर्चुअल वातावरण को अनदेखा करें
    "/__pycache__/", // Python कैश को अनदेखा करें
    "/generated_code/" // जेनरेट किए गए कोड आउटपुट को अनदेखा करें
  ],

  // Haste Map से विशिष्ट मॉड्यूल को अनदेखा करें
  modulePathIgnorePatterns: [
    "<rootDir>/venv/", // Python वर्चुअल वातावरण को अनदेखा करें
    "<rootDir>/src/venv/" // आपके एरर मैसेज से विशिष्ट पथ (playwright-core के लिए)
  ],

  // रेगेक्स पैटर्न का एक ऐरे जिन्हें Jest को टेस्ट फ़ाइलों के लिए उपयोग करना चाहिए
  testMatch: [
    "**/__tests__/**/*.[jt]s?(x)",
    "**/?(*.)+(spec|test).[tj]s?(x)"
  ],

  // इंगित करता है कि रन के दौरान प्रत्येक व्यक्तिगत टेस्ट को रिपोर्ट किया जाना चाहिए या नहीं
  verbose: true,

  // टेस्ट चलाने का वातावरण
  testEnvironment: "jsdom", // ब्राउज़र-जैसे वातावरण के लिए jsdom का उपयोग करें
};