import { SEARCH_RESULTS } from "@/constants";
import {
  AMAR_PORANO_JAHA_CHAY,
  AMAR_NISHITHO_RAATER,
  AMAR_PRANER_MANUS,
  AMAR_HIYAR_MAJHE,
} from "@/constants";

interface ISearchResult {
  id: string;
  title: string;
}

interface ISong {
  id: string;
  domain: string;
  title: string;
  url: string;
  lyrics: string;
  metadata: {
    composition_date?: string;
    poet_age?: string;
    publication_date?: string;
    gitabitan_index?: string;
    raag_taal?: string;
    notation?: string;
    notator?: string;
    raag?: string;
    taal?: string;
    context?: string;
    composition_location?: string;
  };
  citations: string[];
}

const SONG_MAP = {
  "226d66cf-1119-4689-b198-a3f0847804f9": AMAR_PORANO_JAHA_CHAY,
  "bd8c3eba-82bf-46a7-8f18-8a062d46e77c": AMAR_NISHITHO_RAATER,
  "fa710f3f-bd80-4cfa-89c1-ef6c4e0dad65": AMAR_PRANER_MANUS,
  "26c97710-7249-4b36-b26f-4e220d85937f": AMAR_HIYAR_MAJHE,
} as const;

export const getSearchResults = (query: string): ISearchResult[] => {
  if (query.length === 0) return [];
  return SEARCH_RESULTS as ISearchResult[];
};

export const getSongDetails = (id: string): ISong | undefined => {
  // TODO: Later this will be replaced with the actual API call
  return SONG_MAP[id as keyof typeof SONG_MAP];
};
