"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  GeoJSONFeature,
  GeoJSONFeatureCollection,
  GISStats,
  OverlapResponse,
  getGISParcels,
  getNearbyParcels,
  getGISStats,
  detectParcelOverlaps,
  getGISExportUrl,
} from "@/lib/api";
import {
  Search,
  Layers,
  MapPin,
  X,
  Filter,
  Download,
  AlertTriangle,
  RefreshCw,
  Globe2,
  BarChart3,
  Target,
  Shield,
  Satellite,
  Map,
  Navigation2,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Mountain,
} from "lucide-react";

type MapTab = "map" | "analytics" | "overlaps";
type BaseLayer = "osm" | "satellite" | "terrain";

interface SearchResult {
  type: "village" | "geocode";
  name: string;
  district?: string;
  state?: string;
  lat: number;
  lng: number;
  parcelCount?: number;
}

// Comprehensive India geo hierarchy: State → Districts → Villages
// All districts per state (complete list for major Indian states)
const INDIA_DISTRICTS: Record<string, string[]> = {
  "Andhra Pradesh": ["Alluri Sitharama Raju","Anakapalli","Anantapur","Annamayya","Bapatla","Chittoor","East Godavari","Eluru","Guntur","Kakinada","Konaseema","Krishna","Kurnool","Nandyal","NTR","Palnadu","Parvathipuram Manyam","Prakasam","Sri Balaji","Sri Sathya Sai","Srikakulam","Tirupati","Visakhapatnam","Vizianagaram","West Godavari","YSR Kadapa"],
  "Bihar": ["Araria","Arwal","Aurangabad","Banka","Begusarai","Bhagalpur","Bhojpur","Buxar","Darbhanga","East Champaran","Gaya","Gopalganj","Jamui","Jehanabad","Kaimur","Katihar","Khagaria","Kishanganj","Lakhisarai","Madhepura","Madhubani","Munger","Muzaffarpur","Nalanda","Nawada","Patna","Purnia","Rohtas","Saharsa","Samastipur","Saran","Sheikhpura","Sheohar","Sitamarhi","Siwan","Supaul","Vaishali","West Champaran"],
  "Gujarat": ["Ahmedabad","Amreli","Anand","Aravalli","Banaskantha","Bharuch","Bhavnagar","Botad","Chhota Udaipur","Dahod","Dang","Devbhoomi Dwarka","Gandhinagar","Gir Somnath","Jamnagar","Junagadh","Kheda","Kutch","Mahisagar","Mehsana","Morbi","Narmada","Navsari","Panchmahal","Patan","Porbandar","Rajkot","Sabarkantha","Surat","Surendranagar","Tapi","Vadodara","Valsad"],
  "Haryana": ["Ambala","Bhiwani","Charkhi Dadri","Faridabad","Fatehabad","Gurugram","Hisar","Jhajjar","Jind","Kaithal","Karnal","Kurukshetra","Mahendragarh","Nuh","Palwal","Panchkula","Panipat","Rewari","Rohtak","Sirsa","Sonipat","Yamunanagar"],
  "Karnataka": ["Bagalkot","Bangalore Rural","Bangalore Urban","Belagavi","Ballari","Bidar","Chamarajanagar","Chikkaballapura","Chikkamagaluru","Chitradurga","Dakshina Kannada","Davanagere","Dharwad","Gadag","Hassan","Haveri","Kalaburagi","Kodagu","Kolar","Koppal","Mandya","Mysuru","Raichur","Ramanagara","Shivamogga","Tumkur","Udupi","Uttara Kannada","Vijayanagara","Vijayapura","Yadgir"],
  "Kerala": ["Alappuzha","Ernakulam","Idukki","Kannur","Kasaragod","Kollam","Kottayam","Kozhikode","Malappuram","Palakkad","Pathanamthitta","Thiruvananthapuram","Thrissur","Wayanad"],
  "Madhya Pradesh": ["Agar Malwa","Alirajpur","Anuppur","Ashoknagar","Balaghat","Barwani","Betul","Bhind","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Dindori","Guna","Gwalior","Harda","Hoshangabad","Indore","Jabalpur","Jhabua","Katni","Khandwa","Khargone","Mandla","Mandsaur","Morena","Narsinghpur","Neemuch","Niwari","Panna","Raisen","Rajgarh","Ratlam","Rewa","Sagar","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Sidhi","Singrauli","Tikamgarh","Ujjain","Umaria","Vidisha"],
  "Maharashtra": ["Ahmednagar","Akola","Amravati","Aurangabad","Beed","Bhandara","Buldhana","Chandrapur","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur","Mumbai City","Mumbai Suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad","Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindhudurg","Solapur","Thane","Wardha","Washim","Yavatmal"],
  "Odisha": ["Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh","Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi","Kandhamal","Kendrapara","Kendujhar","Khordha","Koraput","Malkangiri","Mayurbhanj","Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Subarnapur","Sundargarh"],
  "Punjab": ["Amritsar","Barnala","Bathinda","Faridkot","Fatehgarh Sahib","Fazilka","Ferozepur","Gurdaspur","Hoshiarpur","Jalandhar","Kapurthala","Ludhiana","Malerkotla","Mansa","Moga","Mohali","Muktsar","Pathankot","Patiala","Rupnagar","Sangrur","Shaheed Bhagat Singh Nagar","Tarn Taran"],
  "Rajasthan": ["Ajmer","Alwar","Banswara","Baran","Barmer","Bharatpur","Bhilwara","Bikaner","Bundi","Chittorgarh","Churu","Dausa","Dholpur","Dungarpur","Ganganagar","Hanumangarh","Jaipur","Jaisalmer","Jalore","Jhalawar","Jhunjhunu","Jodhpur","Karauli","Kota","Nagaur","Pali","Pratapgarh","Rajsamand","Sawai Madhopur","Sikar","Sirohi","Tonk","Udaipur"],
  "Tamil Nadu": ["Ariyalur","Chengalpattu","Chennai","Coimbatore","Cuddalore","Dharmapuri","Dindigul","Erode","Kallakurichi","Kanchipuram","Kanyakumari","Karur","Krishnagiri","Madurai","Mayiladuthurai","Nagapattinam","Namakkal","Nilgiris","Perambalur","Pudukkottai","Ramanathapuram","Ranipet","Salem","Sivaganga","Tenkasi","Thanjavur","Theni","Thoothukudi","Tiruchirappalli","Tirunelveli","Tirupathur","Tiruppur","Tiruvallur","Tiruvannamalai","Tiruvarur","Vellore","Viluppuram","Virudhunagar"],
  "Telangana": ["Adilabad","Bhadradri Kothagudem","Hanamkonda","Hyderabad","Jagtial","Jangaon","Jayashankar Bhupalpally","Jogulamba Gadwal","Kamareddy","Karimnagar","Khammam","Kumuram Bheem Asifabad","Mahabubabad","Mahabubnagar","Mancherial","Medak","Medchal-Malkajgiri","Mulugu","Nagarkurnool","Nalgonda","Narayanpet","Nirmal","Nizamabad","Peddapalli","Rajanna Sircilla","Rangareddy","Sangareddy","Siddipet","Suryapet","Vikarabad","Wanaparthy","Warangal","Yadadri Bhuvanagiri"],
  "Uttar Pradesh": ["Agra","Aligarh","Ambedkar Nagar","Amethi","Amroha","Auraiya","Ayodhya","Azamgarh","Baghpat","Bahraich","Ballia","Balrampur","Banda","Barabanki","Bareilly","Basti","Bhadohi","Bijnor","Budaun","Bulandshahr","Chandauli","Chitrakoot","Deoria","Etah","Etawah","Farrukhabad","Fatehpur","Firozabad","Gautam Buddha Nagar","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hapur","Hardoi","Hathras","Jalaun","Jaunpur","Jhansi","Kannauj","Kanpur Dehat","Kanpur Nagar","Kasganj","Kaushambi","Kushinagar","Lakhimpur Kheri","Lalitpur","Lucknow","Maharajganj","Mahoba","Mainpuri","Mathura","Mau","Meerut","Mirzapur","Moradabad","Muzaffarnagar","Pilibhit","Pratapgarh","Prayagraj","Rae Bareli","Rampur","Saharanpur","Sambhal","Sant Kabir Nagar","Shahjahanpur","Shamli","Shravasti","Siddharthnagar","Sitapur","Sonbhadra","Sultanpur","Unnao","Varanasi"],
  "West Bengal": ["Alipurduar","Bankura","Birbhum","Cooch Behar","Dakshin Dinajpur","Darjeeling","Hooghly","Howrah","Jalpaiguri","Jhargram","Kalimpong","Kolkata","Malda","Murshidabad","Nadia","North 24 Parganas","Paschim Bardhaman","Paschim Medinipur","Purba Bardhaman","Purba Medinipur","Purulia","South 24 Parganas","Uttar Dinajpur"],
};

// Villages per known district (for autocomplete suggestions)
const INDIA_VILLAGES: Record<string, string[]> = {
  "Lucknow": ["Chinhat","Bakshi Ka Talab","Mohanlalganj","Sarojini Nagar","Kakori","Itaunja","Malihabad","Gosainganj","Banthra","Bijnaur"],
  "Agra": ["Fatehabad","Khandauli","Bichpuri","Runkata","Achhnera","Etmadpur","Bah","Fatehpur Sikri","Kiraoli","Pinahat"],
  "Varanasi": ["Sarnath","Chiraigaon","Pindra","Arajiline","Harahua","Sewapuri","Kashi Vidyapeeth","Cholapur","Baragaon","Kashi"],
  "Prayagraj": ["Phulpur","Meja","Soraon","Chaka","Bara","Karchana","Handia","Koraon","Shankargarh","Jasra"],
  "Mathura": ["Vrindavan","Govardhan","Chhata","Mant","Farah","Baldeo","Mahavan","Nandgaon","Barsana","Raya"],
  "Gorakhpur": ["Sahjanwa","Gola","Campierganj","Bhathat","Khorabar","Pipiganj","Bansgaon","Chargawan","Jungle Kaudia","Padrauna"],
  "Patna": ["Danapur","Phulwari","Masaurhi","Barh","Bakhtiyarpur","Mokama","Paliganj","Bikram","Punpun","Naubatpur"],
  "Gaya": ["Bodh Gaya","Sherghati","Nawada","Wazirganj","Amas","Fatehpur","Tekari","Imamganj","Belaganj","Gurua"],
  "Pune": ["Shivajinagar","Hadapsar","Kothrud","Wakad","Baner","Hinjewadi","Aundh","Kondhwa","Wanowrie","Mundhwa","Wagholi","Bavdhan","Ambegaon","Dhayari","Pisoli"],
  "Nashik": ["Igatpuri","Sinnar","Dindori","Niphad","Chandwad","Malegaon","Surgana","Peint","Kalwan","Trimbakeshwar"],
  "Nagpur": ["Kamptee","Hingna","Umred","Katol","Savner","Ramtek","Narkhed","Parseoni","Kuhi","Bhiwapur"],
  "Aurangabad": ["Paithan","Gangapur","Vaijapur","Kannad","Sillod","Soegaon","Khuldabad","Phulambri","Soyegaon","Kanad"],
  "Bhopal": ["Huzur","Berasia","Phanda","Mandideep","Ratibad","Kolar","Shahpura","Fanda","Nayapura","Misrod"],
  "Indore": ["Depalpur","Sanwer","Mhow","Hatod","Betma","Simrol","Sawer","Manpur","Limbodagari","Rau"],
  "Gwalior": ["Lashkar","Morar","Bhitarwar","Dabra","Seondha","Pichhore","Bhander","Gird","Antri","Murar"],
  "Jaipur": ["Sanganer","Amber","Chomu","Phagi","Kotputli","Bassi","Chaksu","Sambhar","Shahpura","Renwal"],
  "Jodhpur": ["Phalodi","Luni","Bilara","Osian","Bhopalgarh","Shergarh","Mandore","Tinwari","Baori","Balesar"],
  "Ahmedabad": ["Daskroi","Dholka","Sanand","Detroj","Bavla","Mandal","Viramgam","Ranpur","Dhandhuka","Barwala"],
  "Surat": ["Bardoli","Kamrej","Chorasi","Olpad","Mangrol","Mahuva","Mandvi","Palsana","Umarpada","Vyara"],
  "Bangalore Urban": ["Anekal","Doddaballapura","Devanahalli","Nelamangala","Hoskote","Magadi","Ramanagara","Kanakapura","Channapatna","Doddballapur"],
  "Mysuru": ["Nanjangud","T. Narasipura","Hunsur","Periyapatna","H.D. Kote","K.R. Nagar","Heggadadevankote","Krishnarajanagara","Jayapura","Sargur"],
  "Chennai": ["Sholinganallur","Alandur","Tambaram","Ambattur","Madhavaram","Tiruvottiyur","Avadi","Thiruvallur","Poonamallee","Pallavaram"],
  "Coimbatore": ["Annur","Mettupalayam","Pollachi","Valparai","Sulur","Kinathukadavu","Perur","Madukkarai","Sarcarsamakulam","Thondamuthur"],
  "Hyderabad": ["Secunderabad","Kukatpally","LB Nagar","Serilingampally","Uppal","Alwal","Kapra","Malkajgiri","Quthbullapur","Rajendranagar"],
  "Thiruvananthapuram": ["Neyyattinkara","Kattakkada","Nedumangad","Varkala","Chirayinkeezhu","Perumathura","Attingal","Kazhakoottam","Nedumangad","Kazhakuttom"],
  "Visakhapatnam": ["Bheemunipatnam","Anakapalle","Paderu","Narsipatnam","Chodavaram","Araku Valley","Chintapalle","Hukumpeta","Koyyuru","Rambilli"],
  "Gurugram": ["Sohna","Pataudi","Farukhnagar","Wazirabad","Manesar","Badshahpur","Kadipur","Bilaspur","Dhankot","Gurgaon"],
  "Ludhiana": ["Samrala","Khanna","Raikot","Jagraon","Dehlon","Payal","Machhiwara","Mullanpur","Sudhar","Pakhowal"],
  "Kolkata": ["Dum Dum","Rajarhat","Behala","Jadavpur","Kasba","Gariahat","Tollygunge","Ballygunge","Shyambazar","Ultadanga"],
  "Khordha": ["Jatni","Bhubaneswar","Bolagarh","Begunia","Chilika","Tangi","Khandagiri","Udayagiri","Khordha","Balianta"],
};

const ALL_STATES = Object.keys(INDIA_DISTRICTS).sort();



const LAND_CLASS_COLORS: Record<string, string> = {
  agricultural: "#16a34a",
  residential: "#2563eb",
  commercial: "#d97706",
  forest: "#065f46",
  wasteland: "#6b7280",
  water: "#0284c7",
  government: "#7c3aed",
  default: "#b45309",
};

function classColor(cls: string | null): string {
  if (!cls) return LAND_CLASS_COLORS.default;
  const key = cls.toLowerCase();
  return Object.entries(LAND_CLASS_COLORS).find(([k]) => key.includes(k))?.[1] ?? LAND_CLASS_COLORS.default;
}

function getDefaultStyle(feat: GeoJSONFeature) {
  const color = classColor(feat.properties.land_classification);
  return { color, weight: 2, opacity: 0.9, fillColor: color, fillOpacity: 0.25 };
}

// ─── Analytics Panel ────────────────────────────────────────────────────────
function AnalyticsPanel({ stats, loading }: { stats: GISStats | null; loading: boolean }) {
  if (loading) return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400 text-xs gap-3">
      <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
      <span>Loading GIS analytics…</span>
    </div>
  );
  if (!stats || stats.error) return (
    <div className="flex flex-col items-center justify-center h-40 text-xs text-gray-400 gap-2">
      <AlertCircle className="w-6 h-6" />
      <span>Statistics not available (PostGIS required)</span>
    </div>
  );

  const coverage = stats.geometry_coverage_pct ?? 0;
  return (
    <div className="p-5 space-y-5 overflow-auto" style={{ maxHeight: 580 }}>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Total Parcels", value: stats.total_records, color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
          { label: "Geo-referenced", value: stats.records_with_geometry, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
          { label: "Coverage", value: `${coverage}%`, color: "text-blue-700", bg: "bg-blue-50 border-blue-200" },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`rounded-xl border p-4 ${bg}`}>
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">{label}</p>
            <p className={`text-2xl font-black mt-1 ${color}`}>{value}</p>
          </div>
        ))}
      </div>
      <div>
        <div className="flex justify-between text-xs text-gray-600 mb-1 font-semibold">
          <span>Geometry Coverage</span><span>{coverage}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden border border-gray-200">
          <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-500" style={{ width: `${coverage}%` }} />
        </div>
      </div>
      {stats.by_district.length > 0 && (
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500 mb-2">Parcels by District</p>
          <div className="space-y-1.5">
            {stats.by_district.slice(0, 8).map(({ district, count }) => (
              <div key={district}>
                <div className="flex justify-between text-xs text-gray-700 mb-0.5">
                  <span className="font-medium">{district}</span>
                  <span className="font-mono text-gray-500">{count}</span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${Math.round((count / stats.total_records) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {stats.by_land_classification.length > 0 && (
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500 mb-2">By Land Classification</p>
          <div className="flex flex-wrap gap-1.5">
            {stats.by_land_classification.map(({ classification, count }) => (
              <span key={classification} className="px-2 py-1 rounded-full text-[10px] font-bold text-white"
                style={{ backgroundColor: classColor(classification) }}>
                {classification} ({count})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Overlaps Panel ──────────────────────────────────────────────────────────
function OverlapsPanel({ data, loading, onRefresh }: { data: OverlapResponse | null; loading: boolean; onRefresh: () => void }) {
  return (
    <div className="p-5 space-y-4 overflow-auto" style={{ maxHeight: 580 }}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-black text-gray-900 uppercase tracking-tight">Parcel Boundary Conflicts</h3>
          <p className="text-[11px] text-gray-500 mt-0.5">PostGIS ST_Intersects overlap detection</p>
        </div>
        <button onClick={onRefresh} className="p-1.5 hover:bg-gray-100 rounded text-gray-500 transition">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>
      {loading && (
        <div className="flex items-center justify-center h-40 text-xs text-gray-400 gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-500" /><span>Running spatial analysis…</span>
        </div>
      )}
      {!loading && data && (
        <>
          <div className={`p-3 rounded-xl border text-xs font-semibold flex items-center gap-2 ${
            data.overlap_count === 0 ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-rose-50 border-rose-200 text-rose-800"
          }`}>
            {data.overlap_count === 0
              ? <><CheckCircle2 className="w-4 h-4" />No overlapping boundaries detected</>
              : <><AlertTriangle className="w-4 h-4" />{data.overlap_count} conflict(s) found</>}
          </div>
          {data.method !== "ST_Intersects_PostGIS" && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-900">
              ⚠️ PostGIS ST_Intersects not available — requires a live PostGIS database.
            </div>
          )}
          <div className="space-y-2">
            {data.overlaps.map((ov, i) => (
              <div key={i} className="p-3 bg-white border border-rose-200 rounded-xl text-xs">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-1.5 py-0.5 bg-rose-100 text-rose-800 font-bold rounded text-[9px] uppercase">Conflict {i + 1}</span>
                  <span className="text-gray-400 text-[10px]">{ov.conflict_type}</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[ov.parcel_a, ov.parcel_b].map((p, pi) => (
                    <div key={pi} className="p-2 bg-gray-50 rounded border border-gray-100">
                      <p className="font-bold text-gray-800">{p.owner ?? "Unknown"}</p>
                      <p className="text-gray-500 font-mono text-[10px]">Survey: {p.survey ?? "—"}</p>
                      <p className="text-gray-400 text-[10px]">{p.village ?? "—"}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Parcel Inspector ────────────────────────────────────────────────────────
// ─── FilterComboBox: type + dropdown autocomplete ───────────────────────────
interface FilterComboBoxProps {
  id: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder: string;
  disabled?: boolean;
  colorClass?: string;
}
function FilterComboBox({ id, value, onChange, options, placeholder, disabled, colorClass }: FilterComboBoxProps) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState(value);
  const ref = React.useRef<HTMLDivElement>(null);

  // Sync external value
  React.useEffect(() => { setQuery(value); }, [value]);

  // Close on outside click
  React.useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filtered = query.length === 0
    ? options.slice(0, 40)
    : options.filter((o) => o.toLowerCase().includes(query.toLowerCase())).slice(0, 30);

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <input
          id={id}
          type="text"
          value={query}
          disabled={disabled}
          placeholder={disabled ? "—" : placeholder}
          autoComplete="off"
          onChange={(e) => {
            setQuery(e.target.value);
            onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => !disabled && setOpen(true)}
          className={`w-full text-[11px] border-2 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:outline-none font-medium transition pr-7 ${
            disabled
              ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
              : colorClass ?? "border-gray-200 bg-white text-gray-800 focus:ring-amber-400 focus:border-amber-500"
          }`}
        />
        {!disabled && (
          <button
            type="button"
            onClick={() => { setOpen(!open); }}
            className="absolute right-2 top-1.5 text-gray-400 hover:text-gray-600"
            tabIndex={-1}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>
      {open && !disabled && filtered.length > 0 && (
        <div className="absolute z-[2000] left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden">
          <div className="max-h-48 overflow-auto">
            {filtered.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => { onChange(opt); setQuery(opt); setOpen(false); }}
                className={`w-full text-left px-3 py-2 text-[11px] hover:bg-amber-50 transition border-b border-gray-50 last:border-0 ${
                  opt === value ? "bg-amber-100 font-bold text-amber-900" : "text-gray-800"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
          {options.length > filtered.length && (
            <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-100 text-[10px] text-gray-400">
              {options.length - filtered.length} more — keep typing to filter
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── ParcelInspector ─────────────────────────────────────────────────────────
function ParcelInspector({ feature, onClose }: { feature: GeoJSONFeature; onClose: () => void }) {
  const p = feature.properties;
  const rows = [
    { label: "Survey No.", value: p.survey_number },
    { label: "Khasra No.", value: p.khasra_number },
    { label: "Khata No.", value: p.khata_number },
    { label: "Plot No.", value: p.plot_number },
    { label: "Owner", value: p.owner_name },
    { label: "Father/Husband", value: p.father_name },
    { label: "Area", value: p.area },
    { label: "Land Type", value: p.land_classification },
    { label: "Village", value: p.village },
    { label: "Tehsil", value: p.tehsil },
    { label: "District", value: p.district },
    { label: "State", value: p.state },
    { label: "Registration No.", value: p.registration_number },
    { label: "Mutation No.", value: p.mutation_number },
    { label: "LRMS ID", value: p.lrms_id },
    { label: "DILRMP ID", value: p.dilrmp_id },
  ].filter((r) => r.value);

  return (
    <div className="absolute top-0 right-0 h-full w-72 bg-white shadow-2xl border-l-4 flex flex-col z-[800] overflow-hidden"
      style={{ borderLeftColor: classColor(p.land_classification) }}>
      <div className="p-4 border-b border-gray-100 flex items-start justify-between gap-2 bg-gradient-to-r from-gray-50 to-white">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Parcel Inspector</p>
          <p className="font-black text-sm text-gray-900 mt-0.5 leading-tight truncate">{p.owner_name ?? "Unknown Owner"}</p>
          <p className="text-xs text-gray-500 font-mono">{p.survey_number ? `Survey ${p.survey_number}` : feature.id}</p>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg transition shrink-0">
          <X className="w-4 h-4 text-gray-400" />
        </button>
      </div>
      {p.land_classification && (
        <div className="px-4 pt-3">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-full text-white uppercase tracking-wide"
            style={{ backgroundColor: classColor(p.land_classification) }}>
            {p.land_classification}
          </span>
        </div>
      )}
      <div className="flex-1 overflow-auto px-4 py-3 space-y-2">
        {rows.map(({ label, value }) => (
          <div key={label} className="flex items-start justify-between gap-2 text-xs border-b border-gray-50 pb-1.5">
            <span className="text-gray-400 font-medium shrink-0 w-28">{label}</span>
            <span className="text-gray-900 font-semibold text-right">{value}</span>
          </div>
        ))}
        {p.centroid_lat && (
          <div className="flex items-start justify-between gap-2 text-xs border-b border-gray-50 pb-1.5">
            <span className="text-gray-400 font-medium shrink-0 w-28">Coordinates</span>
            <span className="text-gray-900 font-mono text-right text-[10px]">
              {p.centroid_lat.toFixed(5)}, {p.centroid_lng?.toFixed(5)}
            </span>
          </div>
        )}
      </div>
      <div className="p-3 border-t border-gray-100 bg-gray-50 text-[10px] text-gray-400 font-mono">ID: {feature.id}</div>
    </div>
  );
}

// ─── Main Map Component ──────────────────────────────────────────────────────
export default function LandMapClient() {
  const mapRef = useRef<any>(null);
  const mapDivRef = useRef<HTMLDivElement>(null);
  const geoJsonLayerRef = useRef<any>(null);
  const nearbyCircleRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  const searchMarkerRef = useRef<any>(null);
  const searchRingRef = useRef<any>(null);
  const nearbyModeRef = useRef(false);

  const [activeTab, setActiveTab] = useState<MapTab>("map");
  const [baseLayer, setBaseLayer] = useState<BaseLayer>("osm");

  const [parcels, setParcels] = useState<GeoJSONFeatureCollection | null>(null);
  const [stats, setStats] = useState<GISStats | null>(null);
  const [overlaps, setOverlaps] = useState<OverlapResponse | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<GeoJSONFeature | null>(null);

  // Filters — State → District → Village hierarchy
  const [filterState, setFilterState] = useState("");
  const [filterDistrict, setFilterDistrict] = useState("");
  const [filterVillage, setFilterVillage] = useState("");
  const [filterClass, setFilterClass] = useState("");

  // Cascading district options from state
  const districtOptions: string[] = filterState && INDIA_DISTRICTS[filterState]
    ? INDIA_DISTRICTS[filterState]
    : Object.values(INDIA_DISTRICTS).flat().sort().filter((v, i, a) => a.indexOf(v) === i);

  // Village options from known district, or all villages as suggestions
  const villageOptions: string[] = filterDistrict && INDIA_VILLAGES[filterDistrict]
    ? INDIA_VILLAGES[filterDistrict]
    : Object.values(INDIA_VILLAGES).flat().sort().filter((v, i, a) => a.indexOf(v) === i);

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  // Nearby
  const [nearbyMode, setNearbyMode] = useState(false);
  const [nearbyRadius, setNearbyRadius] = useState(5000);

  // Status
  const [loadingParcels, setLoadingParcels] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingOverlaps, setLoadingOverlaps] = useState(false);
  const [parcelCount, setParcelCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);

  const TILE_URLS: Record<BaseLayer, { url: string; attribution: string }> = {
    osm: { url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: "© OpenStreetMap" },
    satellite: { url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attribution: "© Esri, Maxar" },
    terrain: { url: "https://tile.opentopomap.org/{z}/{x}/{y}.png", attribution: "© OpenTopoMap" },
  };

  // ── Init Leaflet ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined" || !mapDivRef.current || mapRef.current) return;
    const L = require("leaflet");

    const map = L.map(mapDivRef.current, { center: [22.5937, 78.9629], zoom: 5, zoomControl: false });
    L.control.zoom({ position: "bottomright" }).addTo(map);

    const tile = L.tileLayer(TILE_URLS.osm.url, { attribution: TILE_URLS.osm.attribution, maxZoom: 19 });
    tile.addTo(map);
    tileLayerRef.current = tile;

    // Coord display
    const coordCtrl = L.control({ position: "bottomleft" });
    coordCtrl.onAdd = () => {
      const el = L.DomUtil.create("div");
      el.id = "coord-display";
      el.style.cssText = "background:rgba(15,23,42,0.85);backdrop-filter:blur(4px);color:#94a3b8;padding:4px 10px;font-size:10px;font-family:monospace;border-radius:6px;border:1px solid rgba(148,163,184,0.2)";
      el.innerHTML = "📍 Move cursor over map";
      return el;
    };
    coordCtrl.addTo(map);

    map.on("mousemove", (e: any) => {
      const el = document.getElementById("coord-display");
      if (el) el.innerHTML = `📍 ${e.latlng.lat.toFixed(5)}°N &nbsp; ${e.latlng.lng.toFixed(5)}°E`;
    });

    map.on("click", (e: any) => {
      if (!nearbyModeRef.current) return;
      handleNearbySearch(e.latlng.lat, e.latlng.lng);
    });

    mapRef.current = map;
    setMapReady(true);
  }, []);

  useEffect(() => { nearbyModeRef.current = nearbyMode; }, [nearbyMode]);

  // ── Tile layer switch ────────────────────────────────────────────────────
  useEffect(() => {
    if (!tileLayerRef.current) return;
    tileLayerRef.current.setUrl(TILE_URLS[baseLayer].url);
  }, [baseLayer]);

  // Filter options come from INDIA_GEO local data (cascading, no API call needed)

  // ── Autocomplete suggestions ─────────────────────────────────────────────
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchSuggestions([]); setShowSuggestions(false); return;
    }
    const q = searchQuery.toLowerCase();
    const matches = villageOptions.filter((v) => v.toLowerCase().includes(q)).slice(0, 8);
    setSearchSuggestions(matches);
    setShowSuggestions(matches.length > 0);
  }, [searchQuery, villageOptions]);

  // ── Load parcels ─────────────────────────────────────────────────────────
  const loadParcels = useCallback(async () => {
    if (!mapReady) return;
    setLoadingParcels(true);
    setError(null);
    try {
      const data = await getGISParcels(
        filterVillage || undefined,
        filterDistrict || undefined,
        filterState || undefined,
        filterClass || undefined,
      );
      setParcels(data);
      setParcelCount(data.features.length);
      renderParcels(data);
    } catch (e: any) {
      setError(e.message ?? "Failed to load parcels");
    } finally {
      setLoadingParcels(false);
    }
  }, [mapReady, filterVillage, filterDistrict, filterState, filterClass]);

  useEffect(() => { if (mapReady) loadParcels(); }, [loadParcels]);

  // ── Geocode & navigate when Apply Filters clicked ────────────────────────
  const handleApplyAndNavigate = useCallback(async () => {
    // Always reload parcels
    await loadParcels();

    // Build geocode query from what's filled in
    const parts = [filterVillage, filterDistrict, filterState, "India"].filter(Boolean);
    if (parts.length <= 1) return; // nothing specific to geocode

    const q = parts.join(", ");
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1&addressdetails=1`,
        { headers: { "Accept-Language": "en" } }
      );
      const geo = await res.json();
      if (geo?.[0] && mapRef.current) {
        const lat = parseFloat(geo[0].lat);
        const lng = parseFloat(geo[0].lon);
        const addr = geo[0].address;
        mapRef.current.setView([lat, lng], filterVillage ? 13 : filterDistrict ? 11 : 8, { animate: true, duration: 0.8 });
        const result: SearchResult = {
          type: "geocode",
          name: filterVillage || filterDistrict || filterState,
          district: addr?.district || addr?.state_district || filterDistrict,
          state: addr?.state || filterState,
          lat, lng,
        };
        setSearchResult(result);
        placeSearchPin(lat, lng, result);
      }
    } catch {}
  }, [loadParcels, filterVillage, filterDistrict, filterState]);

  // ── Render GeoJSON ───────────────────────────────────────────────────────
  const renderParcels = (data: GeoJSONFeatureCollection) => {
    if (!mapRef.current) return;
    const L = require("leaflet");
    if (geoJsonLayerRef.current) { mapRef.current.removeLayer(geoJsonLayerRef.current); geoJsonLayerRef.current = null; }
    if (!data.features.length) return;

    const group = L.geoJSON(data, {
      style: (feat: GeoJSONFeature) => getDefaultStyle(feat),
      onEachFeature: (feat: GeoJSONFeature, flayer: any) => {
        const p = feat.properties;
        const color = classColor(p.land_classification);
        const tooltip = `
          <div style="font-family:system-ui;font-size:11px;line-height:1.6;min-width:160px">
            <div style="font-weight:800;color:#1f2937;margin-bottom:2px">${p.owner_name ?? "Unknown Owner"}</div>
            <div style="color:#6b7280;font-size:10px">Survey: <strong style="color:#374151">${p.survey_number ?? "—"}</strong></div>
            <div style="color:#6b7280;font-size:10px">Village: <strong style="color:#374151">${p.village ?? "—"}</strong></div>
            <div style="margin-top:4px">
              <span style="background:${color};color:white;font-size:9px;font-weight:700;padding:1px 7px;border-radius:10px;text-transform:uppercase;letter-spacing:0.05em">
                ${p.land_classification ?? "unclassified"}
              </span>
            </div>
          </div>`;
        flayer.bindTooltip(tooltip, { sticky: true, offset: [12, 0], opacity: 1 });
        flayer.on("click", () => setSelectedFeature(feat));
        flayer.on("mouseover", function (this: any) {
          this.setStyle({ fillOpacity: 0.6, weight: 3.5, opacity: 1 });
          this.bringToFront();
        });
        // FIX: manual style reset — layer.resetStyle() only exists on GeoJSON group, not individual layers
        flayer.on("mouseout", function (this: any) {
          this.setStyle(getDefaultStyle(feat));
        });
      },
    });

    group.addTo(mapRef.current);
    geoJsonLayerRef.current = group;
    try { mapRef.current.fitBounds(group.getBounds(), { padding: [40, 40], maxZoom: 15 }); } catch {}
  };

  // ── Clear search markers ─────────────────────────────────────────────────
  const clearSearchMarker = () => {
    if (!mapRef.current) return;
    if (searchMarkerRef.current) { mapRef.current.removeLayer(searchMarkerRef.current); searchMarkerRef.current = null; }
    if (searchRingRef.current) { mapRef.current.removeLayer(searchRingRef.current); searchRingRef.current = null; }
  };

  // ── Animated search pin ──────────────────────────────────────────────────
  const placeSearchPin = (lat: number, lng: number, result: SearchResult) => {
    if (!mapRef.current) return;
    const L = require("leaflet");
    clearSearchMarker();

    // Pulsing ring
    const ring = L.circle([lat, lng], {
      radius: 600,
      color: "#f59e0b",
      weight: 2.5,
      fillColor: "#fbbf24",
      fillOpacity: 0.15,
      dashArray: "8 5",
    });
    ring.addTo(mapRef.current);
    searchRingRef.current = ring;

    // Custom marker
    const icon = L.divIcon({
      className: "",
      html: `<div style="display:flex;flex-direction:column;align-items:center;pointer-events:none">
        <div style="
          width:42px;height:42px;
          background:linear-gradient(145deg,#f59e0b,#b45309);
          border:3px solid white;
          border-radius:50% 50% 50% 0;
          transform:rotate(-45deg);
          box-shadow:0 6px 24px rgba(245,158,11,0.55),0 2px 8px rgba(0,0,0,0.2);
          display:flex;align-items:center;justify-content:center;
        ">
          <span style="transform:rotate(45deg);font-size:18px;line-height:1">📍</span>
        </div>
        <div style="
          margin-top:8px;
          background:white;
          border:2px solid #f59e0b;
          border-radius:10px;
          padding:5px 12px;
          font-family:system-ui;
          font-size:11px;
          font-weight:800;
          color:#78350f;
          white-space:nowrap;
          box-shadow:0 4px 16px rgba(0,0,0,0.15);
          text-align:center;
          max-width:160px;
          overflow:hidden;
          text-overflow:ellipsis;
        ">
          ${result.name}
          <div style="font-size:9px;font-weight:500;color:#9ca3af;margin-top:1px">
            ${result.type === "village" ? `${result.parcelCount ?? 0} parcel${result.parcelCount !== 1 ? "s" : ""} in DB` : (result.district ?? "OpenStreetMap")}
          </div>
        </div>
      </div>`,
      iconSize: [160, 90],
      iconAnchor: [80, 42],
      popupAnchor: [0, -54],
    });

    const marker = L.marker([lat, lng], { icon });
    marker.addTo(mapRef.current);
    marker.bindPopup(`
      <div style="font-family:system-ui;min-width:220px;padding:0">
        <div style="background:linear-gradient(135deg,#f59e0b,#b45309);color:white;padding:12px 16px;border-radius:8px 8px 0 0;margin:-1px -1px 0">
          <p style="font-size:14px;font-weight:900;margin:0;letter-spacing:-0.01em">${result.name}</p>
          <p style="font-size:10px;opacity:0.85;margin:3px 0 0">${result.type === "village" ? "🗂️ Village — Land Records Database" : "🌐 Location — OpenStreetMap"}</p>
        </div>
        <div style="padding:12px 16px;background:white;border-radius:0 0 8px 8px">
          ${result.district ? `<p style="font-size:11px;color:#374151;margin:0 0 4px"><strong>District:</strong> ${result.district}${result.state ? `, ${result.state}` : ""}</p>` : ""}
          ${result.parcelCount !== undefined ? `<p style="font-size:12px;font-weight:700;color:#d97706;margin:4px 0"><span style="font-size:16px">🗺️</span> ${result.parcelCount} parcel${result.parcelCount !== 1 ? "s" : ""} found</p>` : ""}
          <p style="font-size:10px;color:#9ca3af;margin:8px 0 0;font-family:monospace;border-top:1px solid #f3f4f6;padding-top:8px">${lat.toFixed(6)}°N, ${lng.toFixed(6)}°E</p>
        </div>
      </div>
    `, { maxWidth: 260, className: "gis-search-popup" });
    marker.openPopup();
    searchMarkerRef.current = marker;
  };

  // ── Search handler ───────────────────────────────────────────────────────
  const handleSearch = useCallback(async (query: string) => {
    const q = query.trim();
    if (!q || !mapRef.current) return;

    setSearchLoading(true);
    setShowSuggestions(false);
    setError(null);
    setSearchResult(null);

    // Step 1 — local village match
    const villageMatch = villageOptions.find((v) => v.toLowerCase() === q.toLowerCase())
      || villageOptions.find((v) => v.toLowerCase().includes(q.toLowerCase()));

    if (villageMatch) {
      try {
        const data = await getGISParcels(villageMatch);
        const count = data.features.length;
        let lat = 22.5937, lng = 78.9629;

        if (count > 0) {
          const lats = data.features.map((f) => f.properties.centroid_lat).filter(Boolean) as number[];
          const lngs = data.features.map((f) => f.properties.centroid_lng).filter(Boolean) as number[];
          if (lats.length) lat = lats.reduce((a, b) => a + b, 0) / lats.length;
          if (lngs.length) lng = lngs.reduce((a, b) => a + b, 0) / lngs.length;
        } else {
          // Nominatim for coordinates even if no parcels
          try {
            const geo = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(villageMatch + ", India")}&format=json&limit=1`, { headers: { "Accept-Language": "en" } });
            const geoData = await geo.json();
            if (geoData?.[0]) { lat = parseFloat(geoData[0].lat); lng = parseFloat(geoData[0].lon); }
          } catch {}
        }

        setParcels(data); setParcelCount(count); renderParcels(data);
        mapRef.current.setView([lat, lng], count > 0 ? 13 : 11, { animate: true, duration: 0.8 });

        const district = data.features[0]?.properties.district ?? undefined;
        const state = data.features[0]?.properties.state ?? undefined;
        const result: SearchResult = { type: "village", name: villageMatch, district, state, lat, lng, parcelCount: count };
        setSearchResult(result);
        placeSearchPin(lat, lng, result);
        setSearchLoading(false);
        return;
      } catch {}
    }

    // Step 2 — Nominatim fallback
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q + ", India")}&format=json&limit=1&addressdetails=1`, { headers: { "Accept-Language": "en" } });
      const geo = await res.json();
      if (geo?.[0]) {
        const lat = parseFloat(geo[0].lat), lng = parseFloat(geo[0].lon);
        const addr = geo[0].address;
        mapRef.current.setView([lat, lng], 13, { animate: true, duration: 0.8 });
        const result: SearchResult = {
          type: "geocode",
          name: addr?.village || addr?.town || addr?.city || addr?.county || q,
          district: addr?.district || addr?.state_district,
          state: addr?.state,
          lat, lng,
        };
        setSearchResult(result);
        placeSearchPin(lat, lng, result);
      } else {
        setError(`No results found for "${q}". Try a village, district, or landmark name.`);
      }
    } catch {
      setError("Search failed. Check your network connection.");
    } finally {
      setSearchLoading(false);
    }
  }, [villageOptions]);

  // ── Nearby search ────────────────────────────────────────────────────────
  const handleNearbySearch = async (lat: number, lng: number) => {
    if (!mapRef.current) return;
    const L = require("leaflet");
    if (nearbyCircleRef.current) { mapRef.current.removeLayer(nearbyCircleRef.current); nearbyCircleRef.current = null; }
    const circle = L.circle([lat, lng], {
      radius: nearbyRadius,
      color: "#3b82f6",
      weight: 2,
      fillColor: "#93c5fd",
      fillOpacity: 0.1,
      dashArray: "6 4",
    });
    circle.addTo(mapRef.current);
    nearbyCircleRef.current = circle;

    setLoadingParcels(true);
    try {
      const data = await getNearbyParcels(lat, lng, nearbyRadius);
      setParcels(data); setParcelCount(data.features.length); renderParcels(data);
    } catch (e: any) {
      setError(e.message ?? "Nearby search failed");
    } finally {
      setLoadingParcels(false);
    }
  };

  // ── Stats / Overlaps ─────────────────────────────────────────────────────
  const loadStats = useCallback(async () => {
    setLoadingStats(true);
    try { setStats(await getGISStats()); } catch {} finally { setLoadingStats(false); }
  }, []);

  const loadOverlaps = useCallback(async () => {
    setLoadingOverlaps(true);
    try { setOverlaps(await detectParcelOverlaps(50)); } catch {} finally { setLoadingOverlaps(false); }
  }, []);

  useEffect(() => {
    if (activeTab === "analytics") loadStats();
    if (activeTab === "overlaps") loadOverlaps();
  }, [activeTab]);

  const exportUrl = getGISExportUrl(filterVillage || undefined, filterDistrict || undefined);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col rounded-2xl overflow-hidden border border-gray-200 shadow-xl bg-white">

      {/* ── Dark Header ─────────────────────────────────────────────────── */}
      <div className="bg-slate-900 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3 border-b border-slate-700/60">
        {/* Brand */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-9 h-9 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
            <Globe2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-widest text-amber-400 leading-none">BhumiLekh GIS</p>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5">PostGIS · EPSG:4326 · WGS84</p>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex-1 relative">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400 z-10 pointer-events-none" />
              {searchLoading && <RefreshCw className="w-3.5 h-3.5 absolute right-3 top-2.5 text-amber-400 animate-spin z-10 pointer-events-none" />}
              <input
                type="text"
                id="gis-search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch(searchQuery);
                  if (e.key === "Escape") { setShowSuggestions(false); setSearchQuery(""); clearSearchMarker(); setSearchResult(null); }
                }}
                onFocus={() => searchSuggestions.length > 0 && setShowSuggestions(true)}
                placeholder="Search village, district, or location in India…"
                className="w-full bg-slate-800 border border-slate-600 rounded-xl pl-9 pr-8 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition"
                autoComplete="off"
              />
            </div>
            <button
              onClick={() => handleSearch(searchQuery)}
              disabled={searchLoading || !searchQuery.trim()}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-900 font-bold rounded-xl text-xs transition-all shadow-sm"
            >
              Search
            </button>
            {(searchResult || searchQuery) && (
              <button
                onClick={() => { clearSearchMarker(); setSearchResult(null); setSearchQuery(""); setShowSuggestions(false); }}
                className="px-2.5 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl transition"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Autocomplete dropdown */}
          {showSuggestions && searchSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-16 mt-1.5 bg-white border border-gray-200 rounded-xl shadow-2xl z-[2000] overflow-hidden">
              <div className="px-3 py-2 bg-gradient-to-r from-amber-50 to-amber-100 border-b border-amber-200 flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-amber-600" />
                <p className="text-[10px] font-black text-amber-800 uppercase tracking-wider">Villages in Land Records DB</p>
              </div>
              {searchSuggestions.map((village) => (
                <button
                  key={village}
                  type="button"
                  onClick={() => { setSearchQuery(village); setShowSuggestions(false); handleSearch(village); }}
                  className="w-full text-left px-3.5 py-2.5 hover:bg-amber-50 transition-colors flex items-center justify-between group border-b border-gray-50 last:border-0"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                      <MapPin className="w-3 h-3 text-amber-600" />
                    </div>
                    <span className="text-sm text-gray-800 font-semibold">{village}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-amber-500 transition-colors" />
                </button>
              ))}
              <div className="px-3.5 py-2 bg-gray-50 border-t border-gray-100">
                <p className="text-[10px] text-gray-400">↵ Press Enter to also search OpenStreetMap</p>
              </div>
            </div>
          )}
        </div>

        {/* Parcel count + export */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="text-[10px] font-mono bg-emerald-900/40 text-emerald-300 border border-emerald-700/40 px-2.5 py-1.5 rounded-full flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${loadingParcels ? "bg-amber-400 animate-pulse" : "bg-emerald-400"}`} />
            <span>{loadingParcels ? "Loading…" : `${parcelCount} parcels`}</span>
          </div>
          <a href={exportUrl} download className="p-2 bg-slate-700 hover:bg-slate-600 rounded-xl transition group" title="Download GeoJSON">
            <Download className="w-4 h-4 text-slate-300 group-hover:text-white" />
          </a>
        </div>
      </div>

      {/* ── Search Result Banner ─────────────────────────────────────────── */}
      {searchResult && (
        <div className="bg-gradient-to-r from-amber-500 to-amber-600 px-4 py-2.5 flex items-center justify-between gap-3 border-b border-amber-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center shrink-0">
              <MapPin className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black text-white">{searchResult.name}</span>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                  searchResult.type === "village" ? "bg-white/25 text-white" : "bg-white/20 text-white"
                }`}>
                  {searchResult.type === "village" ? "📂 Land Records DB" : "🌐 OpenStreetMap"}
                </span>
              </div>
              <p className="text-[11px] text-amber-100">
                {searchResult.district}{searchResult.state && `, ${searchResult.state}`}
                {searchResult.parcelCount !== undefined && (
                  <span className="font-bold ml-1.5">· {searchResult.parcelCount} parcel{searchResult.parcelCount !== 1 ? "s" : ""}</span>
                )}
                <span className="font-mono text-amber-200 ml-2 text-[10px]">{searchResult.lat.toFixed(4)}°N {searchResult.lng.toFixed(4)}°E</span>
              </p>
            </div>
          </div>
          <button onClick={() => { clearSearchMarker(); setSearchResult(null); setSearchQuery(""); }}
            className="p-1.5 bg-white/20 hover:bg-white/30 rounded-lg transition shrink-0">
            <X className="w-3.5 h-3.5 text-white" />
          </button>
        </div>
      )}

      {/* ── Tabs ────────────────────────────────────────────────────────── */}
      <div className="flex items-center bg-slate-800 px-4 border-b border-slate-700/60">
        {(["map", "analytics", "overlaps"] as MapTab[]).map((tab) => {
          const Icon = { map: Map, analytics: BarChart3, overlaps: Shield }[tab];
          const label = { map: "Cadastral Map", analytics: "Analytics", overlaps: "Conflict Detection" }[tab];
          return (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-1.5 px-4 py-3 text-[11px] font-bold uppercase tracking-wider transition border-b-2 ${
                activeTab === tab ? "border-amber-400 text-amber-300 bg-slate-700/30" : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-700/20"
              }`}>
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      {/* ── MAP VIEW ────────────────────────────────────────────────────── */}
      {activeTab === "map" && (
        <div className="flex" style={{ height: 620 }}>

          {/* Left Panel */}
          <div className="w-56 shrink-0 bg-gray-50 border-r border-gray-200 flex flex-col overflow-auto z-10">

            {/* Filters — State → District → Village */}
            <div className="p-3 border-b border-gray-200">
              <div className="flex items-center gap-1.5 text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">
                <Filter className="w-3 h-3 text-amber-600" />
                <span>Filter Records</span>
              </div>

              <div className="space-y-2.5">

                {/* 1. State */}
                <div>
                  <label className="text-[9px] font-bold text-amber-700 uppercase tracking-wider block mb-1 flex items-center gap-1">
                    <span className="w-4 h-4 bg-amber-100 rounded text-amber-700 flex items-center justify-center text-[9px] font-black">1</span>
                    State
                  </label>
                  <select
                    id="filter-state"
                    value={filterState}
                    onChange={(e) => {
                      setFilterState(e.target.value);
                      setFilterDistrict("");
                      setFilterVillage("");
                    }}
                    className="w-full text-[11px] border-2 border-amber-200 rounded-lg px-2.5 py-1.5 bg-amber-50 text-gray-800 focus:ring-2 focus:ring-amber-400 focus:border-amber-500 focus:outline-none cursor-pointer font-medium"
                  >
                    <option value="">All States</option>
                    {ALL_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                {/* 2. District — full list + type to search */}
                <div>
                  <label className={`text-[9px] font-bold uppercase tracking-wider block mb-1 flex items-center gap-1 ${
                    filterState ? "text-blue-700" : "text-gray-400"
                  }`}>
                    <span className={`w-4 h-4 rounded text-[9px] font-black flex items-center justify-center ${
                      filterState ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-400"
                    }`}>2</span>
                    District
                    {!filterState && <span className="text-[8px] normal-case font-normal text-gray-400 ml-1">(select state first)</span>}
                  </label>
                  <FilterComboBox
                    id="filter-district"
                    value={filterDistrict}
                    onChange={(v) => { setFilterDistrict(v); setFilterVillage(""); }}
                    options={districtOptions}
                    placeholder="Type or select district…"
                    disabled={!filterState}
                    colorClass="border-blue-200 bg-blue-50 text-gray-800 focus:ring-blue-400 focus:border-blue-500"
                  />
                </div>

                {/* 3. Village — suggestions + free type */}
                <div>
                  <label className={`text-[9px] font-bold uppercase tracking-wider block mb-1 flex items-center gap-1 ${
                    filterDistrict ? "text-emerald-700" : "text-gray-400"
                  }`}>
                    <span className={`w-4 h-4 rounded text-[9px] font-black flex items-center justify-center ${
                      filterDistrict ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-400"
                    }`}>3</span>
                    Village / Locality
                  </label>
                  <FilterComboBox
                    id="filter-village"
                    value={filterVillage}
                    onChange={setFilterVillage}
                    options={villageOptions}
                    placeholder="Type any village name…"
                    colorClass="border-emerald-200 bg-emerald-50 text-gray-800 focus:ring-emerald-400 focus:border-emerald-500"
                  />
                </div>

                {/* Land Type */}
                <div>
                  <label className="text-[9px] font-bold text-gray-500 uppercase tracking-wider block mb-1">Land Type</label>
                  <select
                    id="filter-land-type"
                    value={filterClass}
                    onChange={(e) => setFilterClass(e.target.value)}
                    className="w-full text-[11px] border border-gray-300 rounded-lg px-2.5 py-1.5 bg-white text-gray-800 focus:ring-2 focus:ring-amber-400 focus:border-amber-400 focus:outline-none cursor-pointer"
                  >
                    <option value="">All Types</option>
                    {Object.keys(LAND_CLASS_COLORS).filter((k) => k !== "default").map((c) => (
                      <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <button
                  id="apply-filters-btn"
                  onClick={handleApplyAndNavigate}
                  disabled={loadingParcels}
                  className="w-full py-2 bg-amber-600 hover:bg-amber-700 active:bg-amber-800 text-white font-bold rounded-lg text-[11px] flex items-center justify-center gap-1.5 transition-all shadow-sm disabled:opacity-60"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingParcels ? "animate-spin" : ""}`} />
                  Apply & Go to Location
                </button>

                {(filterState || filterVillage || filterDistrict || filterClass) && (
                  <button
                    onClick={() => { setFilterState(""); setFilterVillage(""); setFilterDistrict(""); setFilterClass(""); }}
                    className="w-full py-1.5 border border-gray-300 hover:border-rose-300 hover:bg-rose-50 text-gray-500 hover:text-rose-600 font-semibold rounded-lg text-[11px] flex items-center justify-center gap-1 transition"
                  >
                    <X className="w-3 h-3" />
                    Clear all filters
                  </button>
                )}
              </div>
            </div>

            {/* Base Layer */}
            <div className="p-3 border-b border-gray-200">
              <div className="flex items-center gap-1.5 text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">
                <Layers className="w-3 h-3 text-amber-600" />
                <span>Base Layer</span>
              </div>
              <div className="space-y-1">
                {(["osm", "satellite", "terrain"] as BaseLayer[]).map((l) => {
                  const Icon = { osm: Map, satellite: Satellite, terrain: Mountain }[l];
                  const label = { osm: "Street Map", satellite: "Satellite", terrain: "Terrain" }[l];
                  return (
                    <button
                      key={l}
                      id={`layer-${l}`}
                      onClick={() => setBaseLayer(l)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[11px] font-semibold transition-all ${
                        baseLayer === l
                          ? "bg-amber-100 text-amber-900 border-2 border-amber-400 shadow-sm"
                          : "text-gray-600 hover:bg-gray-100 border-2 border-transparent"
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${baseLayer === l ? "text-amber-700" : "text-gray-400"}`} />
                      <span>{label}</span>
                      {baseLayer === l && <span className="ml-auto w-2 h-2 bg-amber-500 rounded-full" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Nearby Search */}
            <div className="p-3">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5 text-[10px] font-black text-gray-500 uppercase tracking-widest">
                  <Target className="w-3 h-3 text-amber-600" />
                  <span>Nearby Search</span>
                </div>
                <button
                  id="nearby-toggle"
                  onClick={() => setNearbyMode(!nearbyMode)}
                  className={`text-[9px] font-black px-2.5 py-1 rounded-full transition-all border-2 ${
                    nearbyMode
                      ? "bg-blue-600 text-white border-blue-700 shadow-sm"
                      : "bg-gray-100 text-gray-500 border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {nearbyMode ? "ON" : "OFF"}
                </button>
              </div>

              {nearbyMode ? (
                <div className="space-y-2">
                  <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-lg">
                    <label className="text-[9px] font-bold text-blue-700 uppercase block mb-1.5">
                      Radius: {(nearbyRadius / 1000).toFixed(1)} km
                    </label>
                    <input
                      type="range" min={500} max={50000} step={500}
                      value={nearbyRadius}
                      onChange={(e) => setNearbyRadius(Number(e.target.value))}
                      className="w-full accent-blue-600"
                    />
                    <div className="flex justify-between text-[9px] text-blue-500 mt-0.5 font-mono">
                      <span>0.5km</span><span>50km</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-blue-700 font-semibold">
                    <Navigation2 className="w-3.5 h-3.5" />
                    <span>Click map to search nearby parcels</span>
                  </div>
                </div>
              ) : (
                <p className="text-[10px] text-gray-400">Enable to click any point on the map and find nearby land parcels within a radius.</p>
              )}
            </div>
          </div>

          {/* Map Container */}
          <div className="flex-1 relative">
            {/* Error overlay */}
            {error && (
              <div className="absolute top-3 left-3 right-3 z-[900]">
                <div className="p-3 bg-rose-50 border border-rose-300 text-rose-800 rounded-xl text-xs flex items-start gap-2 shadow-lg">
                  <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                  <div><p className="font-bold mb-0.5">Error</p><p>{error}</p></div>
                  <button onClick={() => setError(null)} className="ml-auto shrink-0">
                    <X className="w-3.5 h-3.5 text-rose-400" />
                  </button>
                </div>
              </div>
            )}

            {/* Loading overlay */}
            {(loadingParcels || searchLoading) && (
              <div className="absolute inset-0 z-[850] flex items-end justify-center pb-6 pointer-events-none">
                <div className="bg-slate-900/90 backdrop-blur px-5 py-2.5 rounded-full shadow-lg text-xs font-bold text-amber-300 flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  {searchLoading ? "Searching…" : "Loading parcels from PostGIS…"}
                </div>
              </div>
            )}

            {/* Leaflet map */}
            <div ref={mapDivRef} className="w-full h-full" onClick={() => setShowSuggestions(false)} />

            {/* Parcel inspector */}
            {selectedFeature && <ParcelInspector feature={selectedFeature} onClose={() => setSelectedFeature(null)} />}
          </div>
        </div>
      )}

      {activeTab === "analytics" && <div style={{ minHeight: 520 }}><AnalyticsPanel stats={stats} loading={loadingStats} /></div>}
      {activeTab === "overlaps" && <div style={{ minHeight: 520 }}><OverlapsPanel data={overlaps} loading={loadingOverlaps} onRefresh={loadOverlaps} /></div>}

      {/* ── Legend (separate row, outside the map) ───────────────────────── */}
      {activeTab === "map" && (
        <div className="border-t border-gray-200 bg-white px-5 py-3">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-1.5 text-[10px] font-black text-gray-500 uppercase tracking-widest shrink-0">
              <div className="w-3 h-3 rounded-sm bg-gradient-to-br from-amber-400 to-amber-600" />
              <span>Land Classification Legend</span>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              {Object.entries(LAND_CLASS_COLORS).filter(([k]) => k !== "default").map(([key, color]) => (
                <div key={key} className="flex items-center gap-1.5 group cursor-default">
                  <div
                    className="w-4 h-4 rounded shadow-sm border-2 border-white ring-1 ring-gray-200 shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-[11px] text-gray-700 font-semibold capitalize group-hover:text-gray-900 transition">
                    {key}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Status Bar ───────────────────────────────────────────────────── */}
      <div className="bg-slate-900 px-4 py-2 flex items-center justify-between text-[10px] font-mono border-t border-slate-700/60">
        <div className="flex items-center gap-4 text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>PostGIS Connected</span>
          </span>
          <span>CRS: EPSG:4326 (WGS84)</span>
          <span>Leaflet v1.9.4</span>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <span>{parcelCount} features</span>
          <span>DILRMP Phase-III · NIC MeghRaj</span>
        </div>
      </div>
    </div>
  );
}
