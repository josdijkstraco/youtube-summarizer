import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import UrlInput from "@/components/UrlInput.vue";

describe("UrlInput", () => {
  it("renders input and submit button", () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });

    expect(wrapper.find("input").exists()).toBe(true);
    expect(wrapper.find("button").text()).toBe("Summarize");
  });

  it("binds input value to v-model", async () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });
    const input = wrapper.find("input");

    await input.setValue("https://www.youtube.com/watch?v=abc123def45");

    expect((input.element as HTMLInputElement).value).toBe(
      "https://www.youtube.com/watch?v=abc123def45",
    );
  });

  it("emits submit event with trimmed URL on form submit", async () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });

    await wrapper.find("input").setValue("  https://youtu.be/abc123def45  ");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toBeTruthy();
    expect(wrapper.emitted("submit")![0]).toEqual([
      "https://youtu.be/abc123def45",
    ]);
  });

  it("does not emit submit when input is empty", async () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });

    await wrapper.find("input").setValue("");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toBeFalsy();
  });

  it("does not emit submit when input is whitespace only", async () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });

    await wrapper.find("input").setValue("   ");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toBeFalsy();
  });

  it("disables button when loading is true", () => {
    const wrapper = mount(UrlInput, { props: { loading: true } });
    const button = wrapper.find("button");

    expect((button.element as HTMLButtonElement).disabled).toBe(true);
  });

  it("disables input when loading is true", () => {
    const wrapper = mount(UrlInput, { props: { loading: true } });
    const input = wrapper.find("input");

    expect((input.element as HTMLInputElement).disabled).toBe(true);
  });

  it("disables button when input is empty", () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });
    const button = wrapper.find("button");

    expect((button.element as HTMLButtonElement).disabled).toBe(true);
  });

  it("enables button when input has text and not loading", async () => {
    const wrapper = mount(UrlInput, { props: { loading: false } });

    await wrapper.find("input").setValue("https://youtu.be/abc123def45");
    const button = wrapper.find("button");

    expect((button.element as HTMLButtonElement).disabled).toBe(false);
  });
});
