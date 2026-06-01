import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import LibraryView from "@/components/LibraryView.vue";
import VideoCard from "@/components/VideoCard.vue";
import type { DownloadedItem } from "@/types";
import * as api from "@/services/api";

vi.mock("@/services/api", () => ({
  fetchDownloaded: vi.fn(),
}));

function makeItem(videoId: string): DownloadedItem {
  return {
    video_id: videoId,
    title: `Title ${videoId}`,
    thumbnail_url: `https://example.com/${videoId}.jpg`,
    downloaded_at: "2026-05-01T00:00:00Z",
  };
}

describe("LibraryView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a VideoCard for each downloaded item on success", async () => {
    vi.mocked(api.fetchDownloaded).mockResolvedValue({
      items: [makeItem("abc123"), makeItem("def456")],
    });
    const wrapper = mount(LibraryView);
    await flushPromises();

    const cards = wrapper.findAllComponents(VideoCard);
    expect(cards).toHaveLength(2);
    expect(wrapper.find(".library__grid").exists()).toBe(true);
  });

  it("shows the empty-state copy and no cards when there are no items", async () => {
    vi.mocked(api.fetchDownloaded).mockResolvedValue({ items: [] });
    const wrapper = mount(LibraryView);
    await flushPromises();

    expect(wrapper.findAllComponents(VideoCard)).toHaveLength(0);
    expect(wrapper.find(".library__grid").exists()).toBe(false);
    expect(wrapper.text()).toContain("No downloaded videos yet");
  });

  it("shows an error message and Retry button, then re-fetches on retry", async () => {
    vi.mocked(api.fetchDownloaded).mockRejectedValueOnce(new Error("boom"));
    const wrapper = mount(LibraryView);
    await flushPromises();

    expect(wrapper.find(".library__status--error").exists()).toBe(true);
    expect(wrapper.text()).toContain("Could not load your library.");
    const retry = wrapper.find(".library__retry");
    expect(retry.exists()).toBe(true);

    vi.mocked(api.fetchDownloaded).mockResolvedValue({
      items: [makeItem("abc123")],
    });
    await retry.trigger("click");
    await flushPromises();

    expect(api.fetchDownloaded).toHaveBeenCalledTimes(2);
    expect(wrapper.find(".library__status--error").exists()).toBe(false);
    expect(wrapper.findAllComponents(VideoCard)).toHaveLength(1);
  });

  it("opens the player in a new tab when a card is played", async () => {
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    vi.mocked(api.fetchDownloaded).mockResolvedValue({
      items: [makeItem("abc123")],
    });
    const wrapper = mount(LibraryView);
    await flushPromises();

    wrapper.findComponent(VideoCard).vm.$emit("play", "abc123");
    await flushPromises();

    expect(openSpy).toHaveBeenCalledWith(
      "/?watch=" + encodeURIComponent("abc123"),
      "_blank",
      "noopener",
    );
    openSpy.mockRestore();
  });
});
