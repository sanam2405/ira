"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function PageContent() {
  const router = useRouter();
  useEffect(() => {
    router.push("/");
  }, [router]);
  return null;
}
