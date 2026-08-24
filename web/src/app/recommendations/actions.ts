"use server";

import { api, ApiError } from "@/lib/api";
import type { InventoryRecommendationResponse } from "@/lib/types";

export type GenerateRecommendationsResult =
  | { ok: true; data: InventoryRecommendationResponse }
  | { ok: false; error: string };

export async function generateRecommendations(): Promise<GenerateRecommendationsResult> {
  try {
    const data = await api.post<InventoryRecommendationResponse>(
      "/ai/inventory-recommendations",
      {}
    );
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) {
      return { ok: false, error: err.message };
    }
    return { ok: false, error: "Could not reach the server." };
  }
}
