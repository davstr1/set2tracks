/**
 * Nunjucks Template Engine Types
 */

export type NunjucksFilterValue = string | number | boolean | object | any[] | null | undefined;

// Note: `any` types below are intentional for Nunjucks filter flexibility
// Filter functions and globals can accept/return any type in template engines
export type NunjucksFilterFunction = (value: NunjucksFilterValue, ...args: any[]) => any;

export interface NunjucksEnvironment {
  addFilter(name: string, func: NunjucksFilterFunction): void;
  addGlobal(name: string, value: any): void;
  render(name: string, context?: object): string;
  renderString(src: string, context?: object): string;
}
