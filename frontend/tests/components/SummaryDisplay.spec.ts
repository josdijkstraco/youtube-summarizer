import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import SummaryDisplay from "@/components/SummaryDisplay.vue";
import type { VideoMetadata } from "@/types";

describe("SummaryDisplay", () => {
  const fullMetadata: VideoMetadata = {
    video_id: "dQw4w9WgXcQ",
    title: "Test Video Title",
    channel_name: "Test Channel",
    duration_seconds: 754,
    thumbnail_url: "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  };

  it("renders summary text", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "This is a test summary." },
    });

    expect(wrapper.text()).toContain("This is a test summary.");
  });

  it("renders multiple paragraphs split by double newlines", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Paragraph one.\n\nParagraph two." },
    });

    const paragraphs = wrapper.findAll(".summary-display__paragraph");
    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0].text()).toBe("Paragraph one.");
    expect(paragraphs[1].text()).toBe("Paragraph two.");
  });

  it("renders Summary heading", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Some text" },
    });

    expect(wrapper.find(".summary-display__heading").text()).toBe("Summary");
  });

  it("renders all metadata fields when provided", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata: fullMetadata },
    });

    expect(wrapper.find(".summary-display__title").text()).toBe(
      "Test Video Title",
    );
    expect(wrapper.find(".summary-display__channel").text()).toBe(
      "Test Channel",
    );
    expect(wrapper.find(".summary-display__duration").text()).toBe("12:34");

    const img = wrapper.find(".summary-display__thumbnail");
    expect(img.exists()).toBe(true);
    expect(img.attributes("src")).toBe(
      "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    );
    expect(img.attributes("alt")).toBe("Test Video Title");
  });

  it("hides metadata section when metadata is null", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata: null },
    });

    expect(wrapper.find(".summary-display__meta").exists()).toBe(false);
  });

  it("hides metadata section when metadata is not provided", () => {
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text" },
    });

    expect(wrapper.find(".summary-display__meta").exists()).toBe(false);
  });

  it("hides title when title is null", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      title: null,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    expect(wrapper.find(".summary-display__title").exists()).toBe(false);
  });

  it("hides channel name when channel_name is null", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      channel_name: null,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    expect(wrapper.find(".summary-display__channel").exists()).toBe(false);
  });

  it("hides duration when duration_seconds is null", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      duration_seconds: null,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    expect(wrapper.find(".summary-display__duration").exists()).toBe(false);
  });

  it("hides thumbnail when thumbnail_url is null", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      thumbnail_url: null,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    expect(wrapper.find(".summary-display__thumbnail").exists()).toBe(false);
  });

  it("formats duration with hours when >= 3600 seconds", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      duration_seconds: 7323,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    // 7323 = 2h 2m 3s → "2:02:03"
    expect(wrapper.find(".summary-display__duration").text()).toBe("2:02:03");
  });

  it("formats short duration without leading zero on minutes", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      duration_seconds: 65,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    // 65 = 1m 5s → "1:05"
    expect(wrapper.find(".summary-display__duration").text()).toBe("1:05");
  });

  it("uses fallback alt text when title is null", () => {
    const metadata: VideoMetadata = {
      ...fullMetadata,
      title: null,
    };
    const wrapper = mount(SummaryDisplay, {
      props: { summary: "Summary text", metadata },
    });

    const img = wrapper.find(".summary-display__thumbnail");
    expect(img.attributes("alt")).toBe("Video thumbnail");
  });
});
