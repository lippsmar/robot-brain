#!/bin/bash
# Grades all final renders with PhotoCraft and lays them out with VectorCraft.
set -e
S=/tmp/claude-0/-home-user/0bed34f3-31b9-556c-a3df-0924702cad8c/scratchpad
P=$S/ext-photocraft/photocraft/target/release/photocraft-cli
V=$S/ext-vectorcraft/vectorcraft/target/release/vectorcraft-cli
R=$S/series-root
mkdir -p $S/pc-work/in $R/graded $R/out

for sc in desk cafe show insight cooling brain analysis; do
  cp $S/render/out/final_$sc.png $S/pc-work/in/
  extra=()
  case $sc in
    cafe)    extra=(--cmd image.adjustments.photoFilter --params '{"filter":"warming85","density":12}') ;;
    insight) extra=(--cmd image.adjustments.photoFilter --params '{"filter":"warming81","density":8}') ;;
    brain)   extra=(--cmd image.adjustments.photoFilter --params '{"filter":"warmingLBA","density":6}') ;;
  esac
  (cd $S/pc-work && timeout 300 $P run in/final_$sc.png \
    --cmd image.adjustments.curves --params '{"points":[[0,6],[64,58],[192,202],[255,250]]}' \
    --cmd image.adjustments.vibrance --params '{"vibrance":16,"saturation":0}' \
    "${extra[@]}" \
    --cmd filter.lensCorrection --params '{"profile":"none","correctDistortion":false,"correctVignette":false,"correctCA":false,"vignetteAmount":-28,"vignetteMidpoint":45}' \
    --cmd filter.sharpen.unsharpMask --params '{"amount":40,"radius":0.8,"threshold":2}' \
    --cmd filter.gallery.filmGrain --params '{"grain":2,"highlightArea":0,"intensity":3}' \
    --out $R/graded/graded_$sc.png > /dev/null)
  echo "graded $sc"
done

cd $R && timeout 900 python3 -I $S/vc-work/scripts/compose_series.py $S/vc-work/scripts $V $R 2>&1 | grep -v 'confined\|MCP server' || true
ls $R/out
