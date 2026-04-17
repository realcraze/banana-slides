// Preset PPT style configuration with i18n support

export interface PresetStyle {
  id: string;
  nameKey: string;  // i18n key for name
  descriptionKey: string;  // i18n key for description
  previewImage?: string;
  color: string;  // accent color for visual indicator
}

// Style IDs map to i18n keys in presetStyles namespace
export const PRESET_STYLES: PresetStyle[] = [
  // {
  //   id: 'business-simple',
  //   nameKey: 'presetStyles.businessSimple.name',
  //   descriptionKey: 'presetStyles.businessSimple.description',
  //   previewImage: '/preset-previews/business-simple.webp',
  //   color: '#0B1F3B',
  // },
  // {
  //   id: 'tech-modern',
  //   nameKey: 'presetStyles.techModern.name',
  //   descriptionKey: 'presetStyles.techModern.description',
  //   previewImage: '/preset-previews/tech-modern.webp',
  //   color: '#7C3AED',
  // },
  {
    id: 'academic-formal',
    nameKey: 'presetStyles.academicFormal.name',
    descriptionKey: 'presetStyles.academicFormal.description',
    previewImage: '/preset-previews/academic-formal.webp',
    color: '#7F1D1D',
  },
  {
    id: 'creative-fun',
    nameKey: 'presetStyles.creativeFun.name',
    descriptionKey: 'presetStyles.creativeFun.description',
    previewImage: '/preset-previews/creative-fun.webp',
    color: '#FF6A00',
  },
  // {
  //   id: 'minimalist-clean',
  //   nameKey: 'presetStyles.minimalistClean.name',
  //   descriptionKey: 'presetStyles.minimalistClean.description',
  //   previewImage: '/preset-previews/minimalist-clean.webp',
  //   color: '#6B7280',
  // },
  // {
  //   id: 'luxury-premium',
  //   nameKey: 'presetStyles.luxuryPremium.name',
  //   descriptionKey: 'presetStyles.luxuryPremium.description',
  //   previewImage: '/preset-previews/luxury-premium.webp',
  //   color: '#F7E7CE',
  // },
  {
    id: 'nature-fresh',
    nameKey: 'presetStyles.natureFresh.name',
    descriptionKey: 'presetStyles.natureFresh.description',
    previewImage: '/preset-previews/nature-fresh.webp',
    color: '#14532D',
  },
  {
    id: 'gradient-vibrant',
    nameKey: 'presetStyles.gradientVibrant.name',
    descriptionKey: 'presetStyles.gradientVibrant.description',
    previewImage: '/preset-previews/gradient-vibrant.webp',
    color: '#2563EB',
  },
  {
    id: 'vintage-poster',
    nameKey: 'presetStyles.vintagePoster.name',
    descriptionKey: 'presetStyles.vintagePoster.description',
    previewImage: '/preset-previews/vintage-poster.png',
    color: '#C54E48',
  },
  {
    id: 'modern-corporate',
    nameKey: 'presetStyles.modernCorporate.name',
    descriptionKey: 'presetStyles.modernCorporate.description',
    previewImage: '/preset-previews/modern-corporate.png',
    color: '#0076D6',
  },
  {
    id: 'urban-geometric',
    nameKey: 'presetStyles.urbanGeometric.name',
    descriptionKey: 'presetStyles.urbanGeometric.description',
    previewImage: '/preset-previews/urban-geometric.png',
    color: '#38B2A6',
  },
  {
    id: 'green-corporate',
    nameKey: 'presetStyles.greenCorporate.name',
    descriptionKey: 'presetStyles.greenCorporate.description',
    previewImage: '/preset-previews/green-corporate.png',
    color: '#529A6E',
  },
  {
    id: 'modern-geometric',
    nameKey: 'presetStyles.modernGeometric.name',
    descriptionKey: 'presetStyles.modernGeometric.description',
    previewImage: '/preset-previews/modern-geometric.png',
    color: '#2E4E70',
  },
  {
    id: 'deep-blue-nexus',
    nameKey: 'presetStyles.deepBlueNexus.name',
    descriptionKey: 'presetStyles.deepBlueNexus.description',
    previewImage: '/preset-previews/deep-blue-nexus.png',
    color: '#1a4d76',
  },
  {
    id: 'minimalist-industrial',
    nameKey: 'presetStyles.minimalistIndustrial.name',
    descriptionKey: 'presetStyles.minimalistIndustrial.description',
    previewImage: '/preset-previews/minimalist-industrial.png',
    color: '#3F5B73',
  },
];

// Helper function to get style with translated values
export const getPresetStyleWithTranslation = (
  style: PresetStyle,
  t: (key: string) => string
): { id: string; name: string; description: string; previewImage?: string } => {
  return {
    id: style.id,
    name: t(style.nameKey),
    description: t(style.descriptionKey),
    previewImage: style.previewImage,
  };
};
