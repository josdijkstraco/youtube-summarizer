import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import LengthSlider from "@/components/LengthSlider.vue";

describe("LengthSlider", () => {
  it("renders with default value and shows '25%' label", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 25 },
    });

    expect(wrapper.find(".length-slider__value").text()).toBe("25%");
    const input = wrapper.find<HTMLInputElement>("input[type='range']");
    expect(input.element.value).toBe("25");
  });

  it("shows correct label at min position (10%)", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 10 },
    });

    expect(wrapper.find(".length-slider__value").text()).toBe("10%");
  });

  it("shows correct label at max position (50%)", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 50 },
    });

    expect(wrapper.find(".length-slider__value").text()).toBe("50%");
  });

  it("emits update:modelValue with correct value on input", async () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 25 },
    });

    const input = wrapper.find<HTMLInputElement>("input[type='range']");
    input.element.value = "35";
    await input.trigger("input");

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    expect(wrapper.emitted("update:modelValue")![0]).toEqual([35]);
  });

  it("renders as disabled when disabled prop is true", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 25, disabled: true },
    });

    const input = wrapper.find<HTMLInputElement>("input[type='range']");
    expect(input.element.disabled).toBe(true);
  });

  it("renders as enabled when disabled prop is false", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 25, disabled: false },
    });

    const input = wrapper.find<HTMLInputElement>("input[type='range']");
    expect(input.element.disabled).toBe(false);
  });

  it("displays label text containing 'Summary length:'", () => {
    const wrapper = mount(LengthSlider, {
      props: { modelValue: 30 },
    });

    expect(wrapper.find(".length-slider__label").text()).toContain(
      "Summary length:",
    );
    expect(wrapper.find(".length-slider__label").text()).toContain("30%");
  });
});
