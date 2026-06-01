import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import VideoCard from "@/components/VideoCard.vue";
import type { DownloadedItem } from "@/types";

// A timestamp a few hours in the past so the relative-time line renders "ago"
// (a fresh timestamp would render "just now").
const downloadedAt = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();

const item: DownloadedItem = {
  video_id: "abc123",
  title: "My Title",
  thumbnail_url: "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
  downloaded_at: downloadedAt,
};

describe("VideoCard", () => {
  it("renders the thumbnail with the correct src", () => {
    const wrapper = mount(VideoCard, { props: { item } });

    const img = wrapper.find(".video-card__thumb");
    expect(img.exists()).toBe(true);
    expect(img.attributes("src")).toBe(
      "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
    );
  });

  it("renders the title text", () => {
    const wrapper = mount(VideoCard, { props: { item } });

    expect(wrapper.text()).toContain("My Title");
  });

  it("renders a Downloaded ... ago date line", () => {
    const wrapper = mount(VideoCard, { props: { item } });

    const date = wrapper.find(".video-card__date");
    expect(date.exists()).toBe(true);
    expect(date.text()).toContain("Downloaded");
    expect(date.text()).toContain("ago");
  });

  it("emits play with the video_id when the card is clicked", async () => {
    const wrapper = mount(VideoCard, { props: { item } });

    await wrapper.trigger("click");

    expect(wrapper.emitted("play")).toBeTruthy();
    expect(wrapper.emitted("play")![0]).toEqual(["abc123"]);
  });

  it("emits play with the video_id when Enter is pressed", async () => {
    const wrapper = mount(VideoCard, { props: { item } });

    await wrapper.get('[role="button"]').trigger("keydown.enter");

    expect(wrapper.emitted("play")).toBeTruthy();
    expect(wrapper.emitted("play")![0]).toEqual(["abc123"]);
  });

  it("falls back to the video_id when title is null", () => {
    const wrapper = mount(VideoCard, {
      props: { item: { ...item, title: null } },
    });

    expect(wrapper.find(".video-card__title").text()).toBe("abc123");
  });
});
