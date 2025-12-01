export interface Weather {
  condition: 'sunny' | 'rainy' | 'foggy';
  wind: Wind;
}

export interface Wind {
  direction: number;
  speed: number;
}