# Regenerates the board from the schematic netlist, checks it, and exports the files to order.
# Uses only what KiCad installs. Run from this folder:  powershell -File build_all.ps1
# Add -Schematic to regenerate the schematic from gen_schematic.py first.
# Do not run after editing the schematic or board by hand in KiCad: it overwrites them.
param([switch]$Schematic)
$bin = "$env:LOCALAPPDATA\Programs\KiCad\10.0\bin"
Set-Location $PSScriptRoot
if ($Schematic) { & "$bin\python.exe" gen_schematic.py }
& "$bin\kicad-cli.exe" sch export netlist --format kicadsexpr -o lockin.net lockin.kicad_sch | Out-Null
& "$bin\python.exe" check_netlist.py lockin.net
& "$bin\kicad-cli.exe" sch erc --severity-all -o erc.rpt lockin.kicad_sch
& "$bin\python.exe" gen_board.py
& "$bin\kicad-cli.exe" pcb drc --severity-all --schematic-parity --refill-zones --save-board -o drc.rpt lockin.kicad_pcb
New-Item -ItemType Directory -Force fab | Out-Null
& "$bin\kicad-cli.exe" pcb export gerbers --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts" --subtract-soldermask -o fab lockin.kicad_pcb | Out-Null
& "$bin\kicad-cli.exe" pcb export drill --format excellon --drill-origin absolute --excellon-units mm --excellon-separate-th -o fab lockin.kicad_pcb | Out-Null
if (Test-Path lockin-gerbers.zip) { [IO.File]::Delete("$PSScriptRoot\lockin-gerbers.zip") }
Compress-Archive -Path fab\* -DestinationPath lockin-gerbers.zip
Remove-Item fab -Recurse -Confirm:$false
& "$bin\kicad-cli.exe" sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Refs,Value,Footprint,Qty' --group-by 'Value,Footprint' -o bom.csv lockin.kicad_sch | Out-Null
& "$bin\kicad-cli.exe" sch export pdf -o lockin-schematic.pdf lockin.kicad_sch | Out-Null
& "$bin\kicad-cli.exe" pcb render --side top --width 1800 --height 1250 -o lockin-board-3d.png lockin.kicad_pcb | Out-Null
"gerbers: lockin-gerbers.zip"
