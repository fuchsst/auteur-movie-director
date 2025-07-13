// Property system types for the Properties Inspector

export enum PropertyType {
  TEXT = 'text',
  NUMBER = 'number',
  SELECT = 'select',
  BOOLEAN = 'boolean',
  COLOR = 'color',
  DATE = 'date',
  FILE = 'file',
  TEXTAREA = 'textarea',
  RANGE = 'range',
  TAGS = 'tags',
  JSON = 'json'
}

export interface SelectOption {
  label: string;
  value: string | number;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: string | number | RegExp;
  message: string;
  validator?: (value: unknown) => boolean;
}

export interface PropertyDefinition {
  key: string;
  label: string;
  type: PropertyType;
  value: string | number | boolean | string[] | Date | null;
  defaultValue?: string | number | boolean | string[] | Date | null;
  description?: string;
  editable: boolean;
  required?: boolean;
  validation?: ValidationRule[];
  options?: SelectOption[]; // For select/radio types
  min?: number; // For number/range types
  max?: number;
  step?: number;
  placeholder?: string;
  group?: string;
  icon?: string;
}

export interface PropertyGroup {
  name: string;
  properties: PropertyDefinition[];
  expanded?: boolean;
  icon?: string;
}

export interface SelectionContext {
  type: 'project' | 'asset' | 'node' | 'scene' | 'shot';
  id: string;
  shotId?: string; // For shot selections - the full shot identifier
  assetType?: 'character' | 'location' | 'style' | 'music';
  metadata?: Record<string, unknown>;
}

export interface PropertyChangeEvent {
  property: PropertyDefinition;
  oldValue: string | number | boolean | string[] | Date | null;
  newValue: string | number | boolean | string[] | Date | null;
  context: SelectionContext;
}
