import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Règle ajoutée par eslint-config-next 16 (React Compiler). Le code existant
      // charge ses données dans des useEffect (setLoading/setX au début de l'effet) :
      // ça fonctionne, mais le refactor dépasse la montée de version — en warning
      // pour l'instant, à traiter au fil de l'eau.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "node_modules/**", ".venv/**", "cache/**"]),
]);
