/**
 * Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * LicenseRef-NvidiaProprietary
 *
 * NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
 * property and proprietary rights in and to this material, related
 * documentation and any modifications thereto. Any use, reproduction,
 * disclosure or distribution of this material and related documentation
 * without an express license agreement from NVIDIA CORPORATION or
 * its affiliates is strictly prohibited
 */
class BrandProgressBar extends HTMLElement {
  constructor() {
    super();
    this.styleEl = document.createElement('style');
  }

  connectedCallback() {
    const container = document.createElement('div', {});
    container.className = 'progress-container';

    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    container.appendChild(progressBar);

    const indicator = document.createElement('div');
    indicator.className = 'indicator';
    progressBar.appendChild(indicator);

    this.updateStyle();

    this.appendChild(this.styleEl);
    this.appendChild(container);
  }
  updateStyle() {
    this.styleEl.textContent = `
      .progress-container {
        align-items: center;
        display: flex;
        flex-direction: column;
        gap: var(--brand-spacing-xs);
        width: 100%;

        .progress-bar {
          background-color: var(--brand-color-feedback-bg-base);
          border: 1px solid var(--brand-color-feedback-border-progress);
          border-radius: 0px;
          height: var(--brand-size-ss);
          width: 100%;

          .indicator {
            animation:2.4s cubic-bezier(0.645, 0.045, 0.355, 1) 0s infinite normal none running indeterminate-animation;
            background-color: var(--brand-color-g500);
            height: 100%;
            width: 100%;
          }
        }
      }
      @keyframes indeterminate-animation {
        0% {
          transform: scaleX(0.015);
          transform-origin: 0% 0%;
        }
        25% {
          transform: scaleX(0.4);
        }
        50% {
          transform: scaleX(0.015);
          transform-origin: 100% 0%;
        }
        75% {
          transform: scaleX(0.4);
        }
        100% {
          transform: scaleX(0.015);
          transform-origin: 0% 0%;
        }
    `;
  }
}
customElements.define('brand-progress-bar', BrandProgressBar);
