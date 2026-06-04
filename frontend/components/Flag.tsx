import "flag-icons/css/flag-icons.min.css";

// Mapping codes IBU/IOC (3 lettres) → ISO 3166-1 alpha-2 (2 lettres)
const IOC_TO_ISO2: Record<string, string> = {
  AFG: "af", ALB: "al", AND: "ad", ARG: "ar", ARM: "am",
  AUS: "au", AUT: "at", BEL: "be", BIH: "ba", BLR: "by",
  BRA: "br", BUL: "bg", CAN: "ca", CHI: "cl", CHN: "cn",
  CRO: "hr", CZE: "cz", DEN: "dk", EST: "ee", FIN: "fi",
  FRA: "fr", GBR: "gb", GEO: "ge", GER: "de", GRE: "gr",
  HUN: "hu", IND: "in", IRL: "ie", ITA: "it", JPN: "jp",
  KAZ: "kz", KGZ: "kg", KOR: "kr", LAT: "lv", LIE: "li",
  LTU: "lt", LUX: "lu", MAR: "ma", MDA: "md", MEX: "mx",
  MGL: "mn", MKD: "mk", NED: "nl", NOR: "no", NZL: "nz",
  POL: "pl", POR: "pt", PUR: "pr", ROU: "ro", RUS: "ru",
  SLO: "si", SRB: "rs", SUI: "ch", SVK: "sk", SWE: "se",
  THA: "th", TPE: "tw", TUR: "tr", UKR: "ua", USA: "us",
  UZB: "uz", GRL: "gl", LIB: "lb",
};

interface Props {
  nation: string;
  className?: string;
}

export default function Flag({ nation, className = "" }: Props) {
  const iso2 = IOC_TO_ISO2[nation]?.toLowerCase();
  if (!iso2) return <span className={`text-xs text-gray-400 ${className}`}>{nation}</span>;
  return (
    <span
      className={`fi fi-${iso2} rounded-sm ${className}`}
      style={{ fontSize: "1.1em", lineHeight: 1 }}
    />
  );
}
