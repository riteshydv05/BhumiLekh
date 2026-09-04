/**
 * Multilingual Translation Dictionary for Indian Government Land Record Portal.
 * Supports English (en), Hindi (hi), and Marathi (mr) with full UI localization.
 */

export const translations: Record<string, Record<string, string>> = {
  en: {
    // Top Bar
    "gov.name": "भारत सरकार | Government of India",
    "gov.skipContent": "Skip to Main Content",
    "gov.highContrast": "High Contrast",
    "gov.highContrastOn": "High Contrast: On",
    "gov.help": "Help",

    // Header
    "header.dept": "भूमि संसाधन विभाग | Department of Land Resources",
    "header.title": "Intelligent Land Record Digitization and Validation System",
    "header.subtitle": "Digital Land Records Management Portal • राष्ट्रीय भू-अभिलेख प्रबंधन",
    "header.aiStatus": "AI Services Active",
    "header.localPipeline": "Local Indic Pipeline",
    "header.operational": "System Status: Operational",

    // Navigation
    "nav.home": "Home",
    "nav.dashboard": "Dashboard",
    "nav.documents": "My Documents",
    "nav.upload": "Upload Document",
    "nav.verify": "Verification",
    "nav.map": "Land Map (GIS)",
    "nav.menu": "Navigation Menu",

    // Home Page Hero
    "hero.tagline": "National Prototype Initiative • SIH / Government Digital Services",
    "hero.title": "Intelligent Land Record Digitization and Validation System",
    "hero.desc": "Upload land records, digitize multilingual documents, extract structured information, validate records, and review results through human-in-the-loop audit pipelines.",
    "hero.uploadBtn": "Upload Land Record",
    "hero.docsBtn": "View My Documents",

    // Quick Services
    "services.title": "Quick Services",
    "services.subtitle": "Citizen & Revenue Officer Portal",
    "services.upload.title": "1. Upload Document",
    "services.upload.desc": "Upload PDF, JPEG, PNG, or TIFF scans of 7/12 extracts, Khasra, Khatauni, or mutation deeds.",
    "services.upload.action": "Upload scan →",
    "services.docs.title": "2. My Documents",
    "services.docs.desc": "Search, filter, and inspect previously digitized land records and review pipeline metadata.",
    "services.docs.action": "Browse records →",
    "services.verify.title": "3. Verify Records",
    "services.verify.desc": "Human-in-the-loop verification console for low-confidence or anomaly-flagged land parcels.",
    "services.verify.action": "Audit & approve →",
    "services.map.title": "4. View Land Map",
    "services.map.desc": "Interactive GIS map with cadastral parcel boundaries, survey coordinates, and ownership spatial queries.",
    "services.map.action": "Open GIS map →",

    // How It Works
    "flow.title": "How It Works: 5-Stage Digitization Flow",
    "flow.subtitle": "Automated offline-first Indic document intelligence with human verification safeguard.",
    "flow.step1.title": "Upload",
    "flow.step1.desc": "High-resolution PDF or scan is uploaded and securely stored in MinIO storage.",
    "flow.step2.title": "AI Processing",
    "flow.step2.desc": "PaddleOCR extracts printed text while TrOCR handles low-contrast handwriting.",
    "flow.step3.title": "Information Extraction",
    "flow.step3.desc": "IndicNER and multilingual parser extract Khasra, Owner, Area, and Dates.",
    "flow.step4.title": "Validation",
    "flow.step4.desc": "Cross-checks numeric formats and runs IsolationForest for suspicious patterns.",
    "flow.step5.title": "Verification",
    "flow.step5.desc": "Revenue officer audits flagged entries in split-screen console to approve records.",

    // Overview Cards
    "overview.ai.title": "Local AI Pipeline",
    "overview.ai.status": "100% Offline-Ready",
    "overview.ai.desc": "PaddleOCR + LayoutLMv3 + IndicNER run locally without mandatory external API dependencies.",
    "overview.db.title": "Database Storage",
    "overview.db.status": "PostgreSQL + PostGIS",
    "overview.db.desc": "Cadastral boundaries and vector embeddings stored with geospatial spatial indexes.",
    "overview.records.title": "Digitized Records",
    "overview.records.status": "Active Registry",
    "overview.records.desc": "All records cataloged with raw OCR preservation and legal identifier protections.",

    // Dashboard
    "dash.title": "Digitization & Validation Dashboard",
    "dash.subtitle": "Live operational metrics and recent document processing queues.",
    "dash.refresh": "Refresh",
    "dash.upload": "Upload Record",
    "dash.totalRecords": "Total Records",
    "dash.processing": "Processing",
    "dash.completed": "Completed",
    "dash.auditRequired": "Audit Required",
    "dash.failed": "Failed",
    "dash.recentTitle": "Recent Documents",
    "dash.viewAll": "View All Records →",

    // Document Table
    "table.filename": "Filename & ID",
    "table.uploadDate": "Upload Date",
    "table.formatSize": "Format / Size",
    "table.language": "Language",
    "table.status": "Processing Status",
    "table.actions": "Actions",
    "table.view": "View",
    "table.verify": "Verify",
    "table.noDocs": "No documents uploaded yet",
    "table.noDocsDesc": "Start by uploading your first land record (7/12 extract, Khasra, Khatauni, or mutation deed).",
    "table.uploadFirst": "Upload Your First Document",

    // Documents Repository
    "docs.title": "Land Records Repository",
    "docs.subtitle": "Browse, filter, and inspect registered land titles and AI extraction results.",
    "docs.search": "Search documents by filename or ID...",
    "docs.allStatuses": "All Statuses",
    "docs.allLanguages": "All Languages",
    "docs.showing": "Showing",
    "docs.of": "of",
    "docs.records": "records",
    "docs.clearFilters": "Clear Filters",

    // Upload Page
    "upload.title": "Upload Land Record Document",
    "upload.subtitle": "Submit scanned land titles, 7/12 extracts, Khasra, Khatauni, or mutation deed documents for automated digitization.",
    "upload.dropzone": "Drag and drop your land record document here, or",
    "upload.browse": "browse your device",
    "upload.formats": "Supported Formats: PDF, JPEG, PNG, TIFF • Maximum File Size: 50 MB",
    "upload.guidelinesTitle": "Official Document Guidelines:",
    "upload.guide1": "Ensure clear scans or high-contrast photos for accurate OCR extraction.",
    "upload.guide2": "Handwritten entries will automatically escalate to TrOCR / VLM interpretation.",
    "upload.guide3": "Multilingual Devanagari (Hindi/Marathi) records are automatically detected and transliterated.",
    "upload.submitBtn": "Start AI Processing",
    "upload.uploadingBtn": "Uploading & Enqueuing...",
    "upload.successTitle": "Document Uploaded Successfully",
    "upload.viewDetails": "View Document Details",
    "upload.goDocs": "Go to My Documents",
    "upload.another": "Upload Another Record",

    // Verification
    "verify.title": "Human-in-the-Loop Verification Console",
    "verify.subtitle": "Review extracted land record fields side-by-side with original scanned documents.",
    "verify.selectRecord": "Select Record:",
    "verify.originalScan": "Original Document Scan",
    "verify.auditForm": "Field Audit & Corrections",
    "verify.auditDesc": "Verify OCR and IndicNER extracted values before committing to registry.",
    "verify.flagBtn": "Flag for Escalation",
    "verify.approveBtn": "Approve & Finalize",

    // Footer
    "footer.desc": "A comprehensive national prototype for multilingual land records digitization, document layout analysis, handwritten record transcription, entity extraction, and cross-validation with automated anomaly detection.",
    "footer.tagline": "Powered by AI-assisted document digitization and validation • Indic Multi-engine Pipeline",
    "footer.services": "Portal Services",
    "footer.legal": "Help & Compliance",
    "footer.copyright": "Intelligent Land Record Digitization and Validation System. All rights reserved.",
  },

  hi: {
    // Top Bar
    "gov.name": "भारत सरकार | Government of India",
    "gov.skipContent": "मुख्य सामग्री पर जाएं",
    "gov.highContrast": "उच्च कंट्रास्ट",
    "gov.highContrastOn": "उच्च कंट्रास्ट: चालू",
    "gov.help": "सहायता",

    // Header
    "header.dept": "भूमि संसाधन विभाग | ग्रामीण विकास मंत्रालय",
    "header.title": "इंटेलिजेंट भू-अभिलेख डिजिटलीकरण एवं सत्यापन प्रणाली",
    "header.subtitle": "डिजिटल भू-अभिलेख प्रबंधन पोर्टल • राष्ट्रीय भू-अभिलेख प्रबंधन",
    "header.aiStatus": "एआई सेवाएं सक्रिय",
    "header.localPipeline": "स्थानीय इंडिक पाइपलाइन",
    "header.operational": "प्रणाली स्थिति: क्रियाशील",

    // Navigation
    "nav.home": "मुख्य पृष्ठ",
    "nav.dashboard": "डैशबोर्ड",
    "nav.documents": "मेरे दस्तावेज़",
    "nav.upload": "दस्तावेज़ अपलोड",
    "nav.verify": "सत्यापन",
    "nav.map": "भू-नक्शा (GIS)",
    "nav.menu": "नेविगेशन मेनू",

    // Home Page Hero
    "hero.tagline": "राष्ट्रीय प्रोटोटाइप पहल • स्मार्ट इंडिया हैकाथॉन / डिजिटल भारत",
    "hero.title": "इंटेलिजेंट भू-अभिलेख डिजिटलीकरण एवं सत्यापन प्रणाली",
    "hero.desc": "भू-अभिलेख अपलोड करें, बहुभाषी दस्तावेज़ों का डिजिटलीकरण करें, संरचित जानकारी निकालें, विसंगतियों की पुष्टि करें और सत्यापन करें।",
    "hero.uploadBtn": "भू-अभिलेख अपलोड करें",
    "hero.docsBtn": "मेरे दस्तावेज़ देखें",

    // Quick Services
    "services.title": "त्वरित नागरिक सेवाएं",
    "services.subtitle": "नागरिक एवं राजस्व अधिकारी पोर्टल",
    "services.upload.title": "१. दस्तावेज़ अपलोड करें",
    "services.upload.desc": "खसरा, खतौनी, ७/१२ नकल अथवा नामांतरण पंजिका (PDF/स्कैन) अपलोड करें।",
    "services.upload.action": "स्कैन अपलोड करें →",
    "services.docs.title": "२. मेरे दस्तावेज़",
    "services.docs.desc": "डिजिटल रूप से संसाधित भू-अभिलेख खोजें, देखें तथा उनकी स्थिति जांचें।",
    "services.docs.action": "दस्तावेज़ सूची देखें →",
    "services.verify.title": "३. रिकॉर्ड सत्यापन",
    "services.verify.desc": "संदिग्ध या कम-विश्वास वाले भू-अभिलेखों का मानव-द्वारा सत्यापन एवं सुधार।",
    "services.verify.action": "जांच व अनुमोदन करें →",
    "services.map.title": "४. भू-नक्शा देखें",
    "services.map.desc": "पार्सल सीमाएं, खसरा नंबर व भू-स्वामित्व देखने हेतु इंटरैक्टिव GIS नक्शा।",
    "services.map.action": "नक्शा खोलें →",

    // How It Works
    "flow.title": "कार्यप्रणाली: ५-चरणीय डिजिटलीकरण प्रक्रिया",
    "flow.subtitle": "स्थानीय इंडिक एआई इंजन द्वारा स्वचालित व सुरक्षित डिजिटलीकरण प्रक्रिया।",
    "flow.step1.title": "अपलोड",
    "flow.step1.desc": "उच्च-रिज़ॉल्यूशन PDF या छवि सुरक्षित MinIO स्टोरेज में सहेजी जाती है।",
    "flow.step2.title": "एआई प्रसंस्करण",
    "flow.step2.desc": "PaddleOCR मुद्रित पाठ निकालता है और TrOCR हस्तलिखित पाठ पढ़ता है।",
    "flow.step3.title": "जानकारी निष्कर्षण",
    "flow.step3.desc": "IndicNER खसरा, स्वामी का नाम, क्षेत्रफल और तारीखें पहचानता है।",
    "flow.step4.title": "सत्यापन एवं विसंगति",
    "flow.step4.desc": "IsolationForest मॉडल संदिग्ध क्षेत्रफल व विसंगतियों की पहचान करता है।",
    "flow.step5.title": "मानव सत्यापन",
    "flow.step5.desc": "राजस्व अधिकारी रिकॉर्ड को ऑडिट कर अंतिम अनुमोदन प्रदान करते हैं।",

    // Overview Cards
    "overview.ai.title": "स्थानीय एआई पाइपलाइन",
    "overview.ai.status": "१००% ऑफलाइन-सक्षम",
    "overview.ai.desc": "PaddleOCR + LayoutLMv3 + IndicNER बिना किसी बाहरी इंटरनेट निर्भरता के स्थानीय रूप से चलते हैं।",
    "overview.db.title": "डेटाबेस स्टोरेज",
    "overview.db.status": "PostgreSQL + PostGIS",
    "overview.db.desc": "स्थानिक पार्सल सीमाएं और वेक्टर एम्बेडिंग सुरक्षित डेटाबेस में संग्रहित।",
    "overview.records.title": "डिजिटलीकृत अभिलेख",
    "overview.records.status": "सक्रिय रजिस्ट्री",
    "overview.records.desc": "मूल OCR पाठ एवं कानूनी पहचानकर्ताओं की अखंडता सुरक्षित रखी जाती है।",

    // Dashboard
    "dash.title": "डिजिटलीकरण एवं सत्यापन डैशबोर्ड",
    "dash.subtitle": "सक्रिय प्रणाली मेट्रिक्स और दस्तावेज़ प्रसंस्करण कतार।",
    "dash.refresh": "रिफ्रेश करें",
    "dash.upload": "दस्तावेज़ अपलोड",
    "dash.totalRecords": "कुल अभिलेख",
    "dash.processing": "प्रगति पर",
    "dash.completed": "सत्यापित",
    "dash.auditRequired": "ऑडिट आवश्यक",
    "dash.failed": "विफल",
    "dash.recentTitle": "हाल के दस्तावेज़",
    "dash.viewAll": "सभी अभिलेख देखें →",

    // Document Table
    "table.filename": "फ़ाइल नाम एवं आईडी",
    "table.uploadDate": "अपलोड दिनांक",
    "table.formatSize": "प्रारूप / आकार",
    "table.language": "पहचानी गई भाषा",
    "table.status": "प्रसंस्करण स्थिति",
    "table.actions": "कार्य",
    "table.view": "देखें",
    "table.verify": "सत्यापित करें",
    "table.noDocs": "अभी तक कोई दस्तावेज़ अपलोड नहीं हुआ",
    "table.noDocsDesc": "अपना पहला भू-अभिलेख (खसरा, खतौनी, ७/१२ या बैनामा) अपलोड करके शुरुआत करें।",
    "table.uploadFirst": "पहला दस्तावेज़ अपलोड करें",

    // Documents Repository
    "docs.title": "भू-अभिलेख भंडार (रिपॉजिटरी)",
    "docs.subtitle": "पंजीकृत भूमि अभिलेख और एआई निष्कर्षण परिणामों को खोजें, फ़िल्टर करें और देखें।",
    "docs.search": "फ़ाइल नाम या आईडी द्वारा दस्तावेज़ खोजें...",
    "docs.allStatuses": "सभी स्थितियां",
    "docs.allLanguages": "सभी भाषाएं",
    "docs.showing": "प्रदर्शित",
    "docs.of": "कुल",
    "docs.records": "अभिलेख",
    "docs.clearFilters": "फ़िल्टर हटाएं",

    // Upload Page
    "upload.title": "भू-अभिलेख दस्तावेज़ अपलोड करें",
    "upload.subtitle": "स्वचालित डिजिटलीकरण हेतु ७/१२, खसरा, खतौनी या नामांतरण दस्तावेज़ सबमिट करें।",
    "upload.dropzone": "यहाँ अपना दस्तावेज़ खींचकर छोड़ें, अथवा",
    "upload.browse": "डिवाइस से फ़ाइल चुनें",
    "upload.formats": "समर्थित प्रारूप: PDF, JPEG, PNG, TIFF • अधिकतम आकार: 50 MB",
    "upload.guidelinesTitle": "आधिकारिक दस्तावेज़ दिशानिर्देश:",
    "upload.guide1": "सटीक OCR निष्कर्षण हेतु साफ़ स्कैन या उच्च-कंट्रास्ट फ़ोटो सुनिश्चित करें।",
    "upload.guide2": "हस्तलिखित प्रविष्टियों को स्वचालित रूप से TrOCR / VLM द्वारा पढ़ा जाएगा।",
    "upload.guide3": "देवनागरी (हिन्दी/मराठी) अभिलेखों का स्वतः भाषा पहचान और लिप्यंतरण होता है।",
    "upload.submitBtn": "एआई प्रसंस्करण प्रारंभ करें",
    "upload.uploadingBtn": "अपलोड हो रहा है...",
    "upload.successTitle": "दस्तावेज़ सफलतापूर्वक अपलोड हुआ",
    "upload.viewDetails": "दस्तावेज़ विवरण देखें",
    "upload.goDocs": "मेरे दस्तावेज़ों पर जाएं",
    "upload.another": "अन्य दस्तावेज़ अपलोड करें",

    // Verification
    "verify.title": "मानव-द्वारा सत्यापन कंसोल (Human-in-the-Loop)",
    "verify.subtitle": "मूल स्कैन दस्तावेज़ के साथ निकाले गए विवरणों का आमने-सामने मिलान व सुधार।",
    "verify.selectRecord": "रिकॉर्ड चुनें:",
    "verify.originalScan": "मूल दस्तावेज़ स्कैन",
    "verify.auditForm": "फ़ील्ड ऑडिट व सुधार",
    "verify.auditDesc": "रजिस्ट्री में जोड़ने से पहले OCR व IndicNER मानों की पुष्टि करें।",
    "verify.flagBtn": "वरिष्ठ अधिकारी को भेजें",
    "verify.approveBtn": "स्वीकृत व अंतिम करें",

    // Footer
    "footer.desc": "बहुभाषी भू-अभिलेख डिजिटलीकरण, लेआउट विश्लेषण, हस्तलिखित पाठ निष्कर्षण तथा विसंगति पहचान हेतु राष्ट्रीय प्रोटोटाइप प्रणाली।",
    "footer.tagline": "एआई-संवर्धित भू-अभिलेख डिजिटलीकरण एवं सत्यापन • स्थानीय इंडिक इंजन",
    "footer.services": "पोर्टल सेवाएं",
    "footer.legal": "सहायता एवं नीतियां",
    "footer.copyright": "इंटेलिजेंट भू-अभिलेख डिजिटलीकरण एवं सत्यापन प्रणाली। सर्वाधिकार सुरक्षित।",
  },

  mr: {
    // Top Bar
    "gov.name": "भारत सरकार | Government of India",
    "gov.skipContent": "मुख्य मजकुराकडे जा",
    "gov.highContrast": "उच्च कॉन्ट्रास्ट",
    "gov.highContrastOn": "उच्च कॉन्ट्रास्ट: चालू",
    "gov.help": "मदत",

    // Header
    "header.dept": "भूमी संसाधन विभाग | ग्रामीण विकास मंत्रालय",
    "header.title": "इंटेलिजंट भू-अभिलेख डिजिटायझेशन व प्रमाणीकरण प्रणाली",
    "header.subtitle": "डिजिटल भू-अभिलेख व्यवस्थापन पोर्टल • राष्ट्रीय भू-अभिलेख प्रणाली",
    "header.aiStatus": "एआय सेवा सक्रिय",
    "header.localPipeline": "स्थानिक इंडिक पाइपलाइन",
    "header.operational": "प्रणाली स्थिती: कार्यरत",

    // Navigation
    "nav.home": "मुख्यपृष्ठ",
    "nav.dashboard": "डॅशबोर्ड",
    "nav.documents": "माझी कागदपत्रे",
    "nav.upload": "दस्तऐवज अपलोड",
    "nav.verify": "पडताळणी",
    "nav.map": "जमीन नकाशा (GIS)",
    "nav.menu": "नेव्हिगेशन मेनू",

    // Home Page Hero
    "hero.tagline": "राष्ट्रीय प्रोटोटाइप उपक्रम • स्मार्ट इंडिया हॅकाथॉन",
    "hero.title": "इंटेलिजंट भू-अभिलेख डिजिटायझेशन व प्रमाणीकरण प्रणाली",
    "hero.desc": "जमिनीचे ७/१२ उतारे, फेरफार नोंदी अपलोड करा, बहुभाषिक कागदपत्रांचे डिजिटायझेशन करा, आणि विसंगतींची पडताळणी करा.",
    "hero.uploadBtn": "जमीन दस्तऐवज अपलोड करा",
    "hero.docsBtn": "माझी कागदपत्रे पहा",

    // Quick Services
    "services.title": "त्वरित नागरिक सेवा",
    "services.subtitle": "नागरिक व महसूल अधिकारी पोर्टल",
    "services.upload.title": "१. दस्तऐवज अपलोड",
    "services.upload.desc": "७/१२ उतारा, ८-अ, फेरफार नोंद किंवा खरेदीखत स्कॅन अपलोड करा.",
    "services.upload.action": "स्कॅन अपलोड करा →",
    "services.docs.title": "२. माझी कागदपत्रे",
    "services.docs.desc": "डिजिटल स्वरूपातील जमिनीच्या नोंदी शोधा आणि स्थिती तपासा.",
    "services.docs.action": "कागदपत्रे पहा →",
    "services.verify.title": "३. नोंदींची पडताळणी",
    "services.verify.desc": "कमी खात्री किंवा विसंगती आढळलेल्या नोंदींची महसूल अधिकाऱ्यांमार्फत पडताळणी.",
    "services.verify.action": "तपासा व मंजूर करा →",
    "services.map.title": "४. जमिनीचा नकाशा",
    "services.map.desc": "गट नंबर, भूखंड सीमा व मालकी पाहण्यासाठी परस्परसंवादी GIS नकाशा.",
    "services.map.action": "नकाशा उघडा →",

    // How It Works
    "flow.title": "कार्यपद्धती: ५-टप्प्यांची डिजिटायझेशन प्रक्रिया",
    "flow.subtitle": "स्थानिक इंडिक एआय इंजिनद्वारे सुरक्षित व स्वयंचलित डिजिटायझेशन.",
    "flow.step1.title": "अपलोड",
    "flow.step1.desc": "७/१२ उतारा किंवा स्कॅन प्रत सुरक्षित MinIO स्टोरेजमध्ये संग्रहित केली जाते.",
    "flow.step2.title": "एआय प्रक्रिया",
    "flow.step2.desc": "PaddleOCR छापील मजकूर वाचतो आणि TrOCR हस्तलिखित नोंदी वाचतो.",
    "flow.step3.title": "माहिती निष्कर्षण",
    "flow.step3.desc": "IndicNER गट क्रमांक, खातेदार, क्षेत्रफळ आणि तारखा ओळखतो.",
    "flow.step4.title": "प्रमाणीकरण",
    "flow.step4.desc": "IsolationForest मॉडेल संशयास्पद क्षेत्रफळ व विसंगती तपासतो.",
    "flow.step5.title": "पडताळणी",
    "flow.step5.desc": "महसूल अधिकारी माहिती तपासून अंतिम मंजुरी देतात.",

    // Overview Cards
    "overview.ai.title": "स्थानिक एआय पाइपलाइन",
    "overview.ai.status": "१००% ऑफलाइन सक्षम",
    "overview.ai.desc": "PaddleOCR + LayoutLMv3 + IndicNER बाह्य इंटरनेटशिवाय पूर्णपणे स्थानिकरीत्या चालतात.",
    "overview.db.title": "डेटाबेस स्टोरेज",
    "overview.db.status": "PostgreSQL + PostGIS",
    "overview.db.desc": "स्थानिक भूखंड सीमा व व्हेक्टर एम्बेडिंग सुरक्षित डेटाबेसमध्ये साठवले जातात.",
    "overview.records.title": "डिजिटायझ्ड नोंदी",
    "overview.records.status": "सक्रिय नोंदवही",
    "overview.records.desc": "मूळ OCR मजकूर आणि कायदेशीर ओळखकर्ते अखंडपणे जतन केले जातात.",

    // Dashboard
    "dash.title": "डिजिटायझेशन व पडताळणी डॅशबोर्ड",
    "dash.subtitle": "थेट प्रणाली मेट्रिक्स आणि दस्तऐवज प्रक्रिया रांग.",
    "dash.refresh": "रिफ्रेश",
    "dash.upload": "नोंद अपलोड करा",
    "dash.totalRecords": "एकूण नोंदी",
    "dash.processing": "प्रक्रियेत",
    "dash.completed": "पूर्ण झाले",
    "dash.auditRequired": "पडताळणी आवश्यक",
    "dash.failed": "अयशस्वी",
    "dash.recentTitle": "अलीकडील दस्तऐवज",
    "dash.viewAll": "सर्व नोंदी पहा →",

    // Document Table
    "table.filename": "फाईल नाव व आयडी",
    "table.uploadDate": "अपलोड दिनांक",
    "table.formatSize": "स्वरूप / आकार",
    "table.language": "ओळखलेली भाषा",
    "table.status": "प्रक्रिया स्थिती",
    "table.actions": "क्रिया",
    "table.view": "पहा",
    "table.verify": "पडताळणी करा",
    "table.noDocs": "अद्याप कोणतेही दस्तऐवज अपलोड केलेले नाहीत",
    "table.noDocsDesc": "तुमचा पहिला ७/१२ उतारा, गट नोंद किंवा फेरफार अपलोड करून सुरुवात करा.",
    "table.uploadFirst": "पहिले दस्तऐवज अपलोड करा",

    // Documents Repository
    "docs.title": "जमीन अभिलेख नोंदणीगार",
    "docs.subtitle": "नोंदणीकृत जमीन अभिलेख आणि एआय निष्कर्ष शोधा, फिल्टर करा आणि तपासा.",
    "docs.search": "फाईल नाव किंवा आयडी द्वारे दस्तऐवज शोधा...",
    "docs.allStatuses": "सर्व स्थिती",
    "docs.allLanguages": "सर्व भाषा",
    "docs.showing": "दर्शवित आहे",
    "docs.of": "एकूण",
    "docs.records": "नोंदी",
    "docs.clearFilters": "फिल्टर काढा",

    // Upload Page
    "upload.title": "जमीन दस्तऐवज अपलोड करा",
    "upload.subtitle": "स्वयंचलित डिजिटायझेशनसाठी ७/१२, फेरफार किंवा खरेदीखत दस्तऐवज सादर करा.",
    "upload.dropzone": "येथे फाईल ड्रॅग करून टाका, किंवा",
    "upload.browse": "डिव्हाइसमधून निवडा",
    "upload.formats": "समर्थित स्वरूप: PDF, JPEG, PNG, TIFF • कमाल आकार: 50 MB",
    "upload.guidelinesTitle": "अधिकृत दस्तऐवज मार्गदर्शक तत्त्वे:",
    "upload.guide1": "अचूक OCR साठी स्पष्ट स्कॅन किंवा उच्च-कॉन्ट्रास्ट फोटो वापरा.",
    "upload.guide2": "हस्तलिखित मजकूर TrOCR / VLM मॉडेलद्वारे स्वयंचलितपणे वाचला जातो.",
    "upload.guide3": "देवनागरी (मराठी/हिंदी) नोंदींची आपोआप भाषा ओळख आणि लिप्यंतरण होते.",
    "upload.submitBtn": "एआय प्रक्रिया सुरू करा",
    "upload.uploadingBtn": "अपलोड होत आहे...",
    "upload.successTitle": "दस्तऐवज यशस्वीरित्या अपलोड झाला",
    "upload.viewDetails": "तपशील पहा",
    "upload.goDocs": "माझ्या कागदपत्रांवर जा",
    "upload.another": "दुसरा दस्तऐवज अपलोड करा",

    // Verification
    "verify.title": "मानवी पडताळणी कन्सोल (Human-in-the-Loop)",
    "verify.subtitle": "मूळ स्कॅन दस्तऐवज आणि काढलेली माहिती समोरासमोर तपासा.",
    "verify.selectRecord": "नोंद निवडा:",
    "verify.originalScan": "मूळ दस्तऐवज स्कॅन",
    "verify.auditForm": "माहिती तपासणी व दुरुस्ती",
    "verify.auditDesc": "नोंदवहीत जतन करण्यापूर्वी OCR आणि IndicNER मूल्यांची खात्री करा.",
    "verify.flagBtn": "वरिष्ठ अधिकाऱ्यांकडे पाठवा",
    "verify.approveBtn": "मंजूर व अंतिम करा",

    // Footer
    "footer.desc": "बहुभाषिक भू-अभिलेख डिजिटायझेशन, लेआउट विश्लेषण, हस्तलिखित मजकूर निष्कर्षण आणि विसंगती पडताळणी प्रणाली.",
    "footer.tagline": "एआय-समर्थित भू-अभिलेख डिजिटायझेशन • स्थानिक इंडिक इंजिन",
    "footer.services": "पोर्टल सेवा",
    "footer.legal": "मदत व कायदेशीर अटी",
    "footer.copyright": "इंटेलिजंट भू-अभिलेख डिजिटायझेशन व प्रमाणीकरण प्रणाली. सर्व हक्क राखीव.",
  },
};

/**
 * Hook to retrieve translated string by key based on active language.
 */
export function getTranslation(lang: string, key: string): string {
  const selectedLang = translations[lang] || translations["en"];
  return selectedLang[key] || translations["en"][key] || key;
}
