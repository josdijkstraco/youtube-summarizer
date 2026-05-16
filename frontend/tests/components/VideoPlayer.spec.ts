import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import VideoPlayer from "@/components/VideoPlayer.vue";
import type { DownloadStatus } from "@/types";
import * as api from "@/services/api";

vi.mock("@/services/api", () => ({
  getDownloadStatus: vi.fn(),
  triggerDownload: vi.fn(),
  getStreamUrl: vi.fn(() => "/api/videos/test-id/stream"),
  deleteDownload: vi.fn(),
}));

function makeStatus(status: DownloadStatus["status"]): DownloadStatus {
  return {
    video_id: "test-id",
    status,
    downloaded_at: null,
    error_message: status === "error" ? "Download failed." : null,
  };
}

describe("VideoPlayer — delete button visibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getStreamUrl).mockReturnValue("/api/videos/test-id/stream");
  });

  it("shows delete button when status is ready", async () => {
    vi.mocked(api.getDownloadStatus).mockResolvedValue(makeStatus("ready"));
    const wrapper = mount(VideoPlayer, {
      props: { videoId: "test-id" },
      attachTo: document.body,
    });
    await flushPromises();

    expect(wrapper.find(".video-player__btn--destructive").exists()).toBe(true);
    wrapper.unmount();
  });

  it("hides delete button when status is idle (no record exists)", async () => {
    vi.mocked(api.getDownloadStatus).mockRejectedValue(new Error("no record"));
    const wrapper = mount(VideoPlayer, {
      props: { videoId: "test-id" },
      attachTo: document.body,
    });
    await flushPromises();

    expect(wrapper.find(".video-player__btn--destructive").exists()).toBe(false);
    wrapper.unmount();
  });

  it("hides delete button when status is pending", async () => {
    vi.mocked(api.getDownloadStatus).mockResolvedValue(makeStatus("pending"));
    const wrapper = mount(VideoPlayer, {
      props: { videoId: "test-id" },
      attachTo: document.body,
    });
    await flushPromises();

    expect(wrapper.find(".video-player__btn--destructive").exists()).toBe(false);
    wrapper.unmount();
  });

  it("hides delete button when status is error", async () => {
    vi.mocked(api.getDownloadStatus).mockResolvedValue(makeStatus("error"));
    const wrapper = mount(VideoPlayer, {
      props: { videoId: "test-id" },
      attachTo: document.body,
    });
    await flushPromises();

    expect(wrapper.find(".video-player__btn--destructive").exists()).toBe(false);
    wrapper.unmount();
  });

  it("hides delete button when status is null", async () => {
    vi.mocked(api.getDownloadStatus).mockResolvedValue(makeStatus(null));
    const wrapper = mount(VideoPlayer, {
      props: { videoId: "test-id" },
      attachTo: document.body,
    });
    await flushPromises();

    expect(wrapper.find(".video-player__btn--destructive").exists()).toBe(false);
    wrapper.unmount();
  });
});
