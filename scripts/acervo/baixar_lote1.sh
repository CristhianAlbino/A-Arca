#!/usr/bin/env bash
# Uso (Git Bash):  bash scripts/acervo/baixar_lote1.sh "$TEMP/arca-downloads" "/g/Meu Drive/ARCA"
# Pode rodar de novo a qualquer momento: retoma downloads parciais, pula os completos e nunca
# sobrescreve o que já está no Drive. Itens aprovados pelo usuário em 2026-11-18.
set -u
STAGE="$1"
ARCA="$2"
mkdir -p "$STAGE"
K="https://download.kiwix.org/zim"

# url | destination subfolder | expect published .sha256 (1/0)
ITEMS=(
  "https://ebible.org/epub/porbr2018.epub|12_ENTRETENIMENTO/01_Biblia|0"
  "$K/wikivoyage/wikivoyage_pt_all_nopic_2026-09.zim|02_ENCICLOPEDIAS|1"
  "$K/wikibooks/wikibooks_pt_all_nopic_2026-10.zim|02_ENCICLOPEDIAS|1"
  "$K/wikipedia/wikipedia_pt_medicine_nopic_2026-10.zim|02_ENCICLOPEDIAS|1"
  "$K/wiktionary/wiktionary_pt_all_nopic_2026-09.zim|02_ENCICLOPEDIAS|1"
  "$K/wikipedia/wikipedia_pt_all_nopic_2026-05.zim|02_ENCICLOPEDIAS|1"
)

for entry in "${ITEMS[@]}"; do
  IFS='|' read -r url sub has_sum <<< "$entry"
  name="$(basename "$url")"
  file="$STAGE/$name"
  echo "== $name: baixando"
  # -C - resumes a partial file; retries cover short network drops.
  remote="$(curl -sIL --fail "$url" | tr -d $'' | awk 'tolower($1)=="content-length:" {n=$2} END {print n}')"
  local_size="$(stat -c %s "$file" 2>/dev/null || echo 0)"
  if [ -n "$remote" ] && [ "$local_size" = "$remote" ]; then
    echo "   já completo ($local_size bytes), sem baixar de novo"
  elif ! curl -L --fail --retry 5 --retry-delay 10 -C - -o "$file" "$url" --silent --show-error; then
    echo "FALHA download $name"; continue
  fi
  # Read from stdin: Git Bash's sha256sum prefixes the hash with "\" for Windows paths.
  actual="$(sha256sum < "$file" | cut -d' ' -f1)"
  if [ "$has_sum" = "1" ]; then
    expected="$(curl -sL --fail "$url.sha256" | cut -d' ' -f1)"
    if [ -z "$expected" ] || [ "$expected" != "$actual" ]; then
      echo "FALHA sha256 $name esperado=$expected obtido=$actual"; continue
    fi
    echo "OK sha256 confere (publicado) $name $actual"
  else
    echo "OK sha256 calculado (sem checksum publicado) $name $actual"
  fi
  dest="$ARCA/$sub"
  mkdir -p "$dest"
  if [ -e "$dest/$name" ]; then
    echo "JA EXISTE $dest/$name (não sobrescrito)"; continue
  fi
  mv "$file" "$dest/$name" && echo "MOVIDO $name -> $sub ($(du -h "$dest/$name" | cut -f1))"
done
echo "== FIM DO LOTE 1"
