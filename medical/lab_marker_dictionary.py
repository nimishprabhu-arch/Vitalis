MARKER_RULES = [
    ("Fasting Blood Sugar", "Glucose", ["fasting blood sugar", "fasting glucose", "fbs"]),
    ("Post Prandial Blood Sugar", "Glucose", ["post prandial blood sugar", "post prandial glucose", "ppbs", "pp blood sugar"]),
    ("HbA1c", "Glucose", ["hba1c", "hb a1c", "glycosylated hb", "glycosylated haemoglobin", "glycosylated hemoglobin"]),
    ("Estimated Average Glucose", "Glucose", ["estimated average glucose", "eag"]),

    ("Total Cholesterol", "Lipids", ["cholesterol", "total cholesterol"]),
    ("Triglycerides", "Lipids", ["triglyceride", "triglycerides"]),
    ("HDL", "Lipids", ["hdl - cholesterol", "hdl cholesterol", "hdl"]),
    ("LDL", "Lipids", ["ldl - cholesterol", "ldl cholesterol", "ldl"]),
    ("VLDL", "Lipids", ["vldl"]),
    ("Cholesterol/HDL Ratio", "Lipids", ["cholesterol/hdl ratio", "cholesterol hdl ratio"]),
    ("LDL/HDL Ratio", "Lipids", ["ldl / hdl ratio", "ldl/hdl ratio", "ldl hdl ratio"]),

    ("Hemoglobin", "CBC", ["hemoglobin", "haemoglobin", "hb"]),
    ("WBC", "CBC", ["wbc", "white blood cells", "total leucocyte count", "total leukocyte count", "tlc"]),
    ("RBC", "CBC", ["rbc", "red blood cells", "red blood cell count"]),
    ("Platelet Count", "CBC", ["platelet", "platelet count", "platelets"]),
    ("Hematocrit", "CBC", ["hematocrit", "haematocrit", "pcv"]),
    ("MCV", "CBC", ["mcv"]),
    ("MCH", "CBC", ["mch"]),
    ("MCHC", "CBC", ["mchc"]),
    ("RDW", "CBC", ["rdw"]),

    ("AST", "Liver", ["ast", "sgot", "aspartate transaminase"]),
    ("ALT", "Liver", ["alt", "sgpt", "alanine transaminase"]),
    ("GGT", "Liver", ["ggt", "gamma gt", "gamma glutamyl transferase"]),
    ("Alkaline Phosphatase", "Liver", ["alkaline phosphatase", "alp"]),
    ("Bilirubin", "Liver", ["bilirubin", "total bilirubin"]),
    ("Direct Bilirubin", "Liver", ["direct bilirubin"]),
    ("Indirect Bilirubin", "Liver", ["indirect bilirubin"]),
    ("Total Protein", "Liver", ["total protein"]),
    ("Albumin", "Liver", ["albumin"]),
    ("Globulin", "Liver", ["globulin"]),

    ("Creatinine", "Kidney", ["creatinine", "serum creatinine"]),
    ("Urea", "Kidney", ["urea", "blood urea"]),
    ("Uric Acid", "Kidney", ["uric acid"]),
    ("BUN", "Kidney", ["bun", "blood urea nitrogen"]),
    ("eGFR", "Kidney", ["egfr", "e-gfr"]),

    ("TSH", "Thyroid", ["tsh", "thyroid stimulating hormone"]),
    ("T3", "Thyroid", ["t3", "total t3", "triiodothyronine"]),
    ("T4", "Thyroid", ["t4", "total t4", "thyroxine"]),
    ("Free T3", "Thyroid", ["free t3", "ft3"]),
    ("Free T4", "Thyroid", ["free t4", "ft4"]),

    ("Vitamin D", "Vitamins", ["vitamin d", "25 hydroxy vitamin d", "25-oh vitamin d"]),
    ("Vitamin B12", "Vitamins", ["vitamin b12", "b12"]),

    ("HBsAg", "Infectious Disease", ["australia antigen", "hbsag", "hbs ag", "hepatitis b surface antigen"]),
    ("HIV", "Infectious Disease", ["hiv", "hiv 1", "hiv 2", "hiv i", "hiv ii", "hiv 1 & 2", "hiv 1 and 2"]),
    ("HCV", "Infectious Disease", ["hcv", "anti hcv", "hepatitis c"]),
    ("VDRL", "Infectious Disease", ["vdrl", "syphilis"]),
    ("TB", "Infectious Disease", ["tb", "tuberculosis", "quantiferon", "tb gold", "interferon gamma"]),

    ("Urine Sugar", "Urine", ["urine sugar", "fasting urine sugar", "post prandial urine sugar"]),
    ("Urine Ketones", "Urine", ["urine acetone", "urine ketone", "fasting urine aceton", "post prandial urine acetone"]),
]


def normalize_text(value: str) -> str:
    return " ".join((value or "").lower().replace("-", " ").replace("_", " ").split())


def canonicalize_marker(raw_marker: str, fallback_panel: str | None = None) -> tuple[str, str]:
    normalized_raw = normalize_text(raw_marker)

    for canonical_marker, category, aliases in MARKER_RULES:
        if normalized_raw == normalize_text(canonical_marker):
            return canonical_marker, category

        for alias in aliases:
            if normalized_raw == normalize_text(alias):
                return canonical_marker, category

    return raw_marker.strip(), fallback_panel or "Uncategorized"