import { SEARCH_RESULTS } from "@/constants";

interface ISearchResult {
  id: string;
  title: string;
}

export const getSearchResults = (query: string): ISearchResult[] => {
  if (query.length === 0) return [];
  return SEARCH_RESULTS as ISearchResult[];
};
