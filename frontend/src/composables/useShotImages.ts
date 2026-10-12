/** 分镜配图归一：新 images 数组优先，老单图 image 回退。 */
export function imgUrl(name: string) { return `/api/images/${name}` }
export function shotImgs(s: any): any[] {
  if (!s) return []
  if (s.images && s.images.length) return s.images
  if (s.image) return [{ name: s.image, kind: 'ref' }]
  return []
}
export function firstImg(s: any) { return shotImgs(s).find(x => x.kind === 'first') || null }
export function refImgs(s: any) { return shotImgs(s).filter(x => x.kind !== 'first') }

const CROPS = [
  { label: '大特写', value: 'extreme_close' }, { label: '特写', value: 'closeup' },
  { label: '近景', value: 'close' }, { label: '中近景', value: 'medium_close' },
  { label: '中景', value: 'medium' }, { label: '中全景', value: 'medium_full' },
  { label: '全景', value: 'full' }, { label: '远景', value: 'wide' },
  { label: '大远景', value: 'extreme_wide' },
]
export function cropLabel(s: any) { return (CROPS.find(c => c.value === s.camera?.crop) || {} as any).label || s.camera?.crop || '' }
