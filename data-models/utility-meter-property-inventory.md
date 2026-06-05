# Utility Electric Meter — Property Inventory (research scratch)

**Status:** exploratory scratch, not a data-model document. Built from a read-pass through the GEISA project's metering schemas and specification, to support drafting an eBus `utility-meter` data-model on branch `wip/data-model-utility-meter`.

## Sources

All paths below are within the locally cloned GEISA project (`~/projects/GEISA/repo/`):

- `specification/source/api/discovery.rst` — Platform Discovery; "Metrology Hardware" section enumerates the static nameplate the host must publish for Meter-type devices.
- `specification/source/api/instantaneous.csv` — 58-row table of instantaneous metering quantities with units, datatype, and mandatory/optional flag per device-type (AC Polyphase Meter / AC Meter / Unspecified).
- `specification/source/api/instantaneous.rst` — narrative on the ≥1 Hz instantaneous push: arithmetic vs. vectorial calculation conventions, device-type gating.
- `schemas/metered_quantities.proto` — protobuf message definitions: `GeisaBillingQuantities_Summation_Total` (47 energy fields), `GeisaBillingQuantities_Demand_Total` (47 max-demand fields with timestamps), `GeisaTypeInstantaneousQuantities_System` / `_PerPhase` / `_Other`, `GeisaInstantaneousQuantities_Harmonic`.
- `specification/source/api/status.rst` — platform/app status. Only the "Power Degraded" / "Power Loss" runtime events are meter-relevant; the rest is GEISA-host lifecycle.

## Out of scope for eBus utility-meter

Per direction on 2026-06-05, the high-sample-rate waveform path is explicitly excluded — eBus utility-meter targets the ~1 Hz instantaneous tier and the slower billing/demand tier. The following GEISA artifacts are noted for completeness but not mined for properties:

- `schemas/waveform.proto`, `specification/source/api/waveform.rst` — waveform stream descriptors, samples-per-cycle, alignment metadata for voltage/current sample streams.
- `GeisaInstantaneousQuantities_Harmonic` (partially in scope — see "Power Quality" group below; the per-bin `repeated float harmonic_Voltage / harmonic_Current` arrays straddle the line and are deferred).

Also out of scope: GEISA's MQTT topic-tree layout, protobuf-vs-Homie message framing, the LEE/ADM application-isolation model. Those are GEISA architecture concerns, not utility-meter property concerns.

## Property groups

Properties are grouped by lifecycle and update cadence, which roughly maps to how Homie capabilities (nodes) would partition them in an eBus data-model. Annotations:

- **GEISA-M** = mandatory for AC Polyphase Meter device type per `instantaneous.csv`.
- **GEISA-O** = optional in GEISA but commonly present.
- Units follow GEISA usage; `micro` prefixes in the proto reflect integer-scaling choices and are not meaningful at the eBus property level.

### 1. Identity & nameplate (static; retained on broker)

From `discovery.rst` "Hardware, Firmware, and Platform Software" + "Metrology Hardware":

- Device type discriminator (electric meter, EV charger, etc.)
- Manufacturer name, model, hardware revision, serial number(s)
- Firmware/OS versions
- Operator name and operator-assigned device identifier (if provisioned)
- **Meter Rating / Class**
- **Meter Form** (ANSI form number — 2S, 3S, 9S, 16S, etc.; identifies CT/PT/blade configuration)
- **Number of phases** and whether **neutral is connected**
- **Nominal phase angle** (120° for three-phase wye, 180° for split-phase, etc.)
- **Nominal frequency** (50 / 60 Hz)
- **Nominal phase-to-phase voltage** (when applicable)
- **Nominal phase-to-neutral voltage** (when applicable)
- Calculation convention: arithmetic vs. vectorial (jurisdictional — e.g., Canada prefers vectorial)

Mappable to an eBus `nameplate` capability or onto top-level device attributes; the form/phase/voltage trio especially is the static frame against which all the live measurements are interpreted.

### 2. Instantaneous measurements (push ≥ 1 Hz)

The shape is "per-phase × {V, I, P, Q, S(4 quadrants)} + system aggregates + angles/PF/THD". GEISA serializes this as one `GeisaInstantaneousQuantities` message containing four `_PerPhase` sub-messages (A, B, C, N) plus an `_Other` for neutral-imputed/load-side and frequency/temperature at the top.

**Per-phase (A, B, C, and where present N):**

- RMS voltage — GEISA-M for phase A, GEISA-O for B/C on single-phase
- RMS current — GEISA-M for phase A, GEISA-O for B/C on single-phase
- Active power delivered (W)
- Active power received (W)
- Reactive power delivered (VAR)
- Reactive power received (VAR)
- Apparent power in each of the four quadrants Q1 / Q2 / Q3 / Q4 (VA)
- Voltage phase angle (degrees, referenced to phase A)
- Current phase angle (degrees, referenced to same-phase voltage)
- Power factor
- Power factor angle
- THD (voltage) — percentage
- THD (current) — percentage
- TDD (current) — percentage; total demand distortion, distinct from THD
- Fundamental-only RMS V and RMS I (in addition to fundamental + harmonics)
- 2nd-harmonic V and I (broken out because it's the most-watched harmonic — inrush, transformer saturation)
- Distortion current RMS

**System aggregates:**

- Line frequency (Hz) — GEISA-M
- System active power W (sum / net / delivered / received)
- System reactive power VAR (Q1/Q2/Q3/Q4 plus sums)
- System apparent power VA — arithmetic and vectorial flavors
- System power factor — arithmetic and vectorial
- System power factor angle — arithmetic and vectorial

**Other:**

- Neutral RMS current (measured)
- Neutral RMS current (imputed from A+B+C)
- Load-side voltage (some meters expose both line- and load-side voltage)
- Internal meter temperature (°C) — appears at the top of `GeisaInstantaneousQuantities`

### 3. Billing energy totals (summation; slow cadence, monotonic-ish)

From `GeisaBillingQuantities_Summation_Total` (47 fields). Pattern is `{active | reactive | apparent} × {delivered | received | sum | net} × {fundamental+harmonics | fundamental-only}`, with reactive energy further split by quadrant. The eBus data-model will not need every variant of this matrix on day one, but the slots should be open.

Key axes:

- **Active energy (Wh)**: delivered, received, sum, net — both "fundamental + harmonics" and "fundamental only" variants.
- **Reactive energy (VARh)**: delivered, received, sum, net; per-quadrant Q1, Q2, Q3, Q4; quadrant-pair sums (Q1+Q4, Q2+Q3); quadrant-pair differences (Q1−Q4, Q3−Q2, Q2−Q3); each in both fundamental+harmonics and fundamental-only flavors. The quadrant-pair quantities are what regulated tariffs increasingly bill on.
- **Apparent energy (VAh)**: delivered, received, sum — arithmetic and vectorial computations. Vectorial uses √(Wh² + VARh²) with various reactive-quadrant pairings.
- **Power-factor (energy-derived)**: PF computed from billing-period Wh and VAh — separate arithmetic and vectorial calculations.

Every field carries a microsecond UNIX timestamp at the message level.

### 4. Demand maxima (per integration interval)

From `GeisaBillingQuantities_Demand_Total` — same 47-element axis structure as summation, but each field is a `GeisaTypeMaxDemand { maxDemandTime, quantity }`: the peak average over the demand-integration window (typically 15 min) and the timestamp at which the peak occurred. This is the basis for demand-charge billing in commercial tariffs.

The eBus data-model will need to expose:

- Current-interval demand (running)
- Most-recent-interval demand
- Period-to-date peak demand and its timestamp
- The demand-integration window itself as a configuration property (so consumers know what `15-min average` actually means here)

### 5. Power quality (per-phase, ≥ 1 Hz)

These overlap with §2 but are worth calling out as their own capability because they have a different audience (PQ analytics, not energy billing):

- THD voltage / THD current per phase
- TDD current per phase
- 2nd-harmonic V and I per phase (explicit, because the rest of the spectrum is bulk-encoded)
- Higher-order harmonic spectra (deferred; GEISA encodes these as `repeated float` arrays — straddles the waveform line we agreed to skip in v0)

### 6. Meter-relevant status & events

Per `status.rst`, most platform/app status messages concern the GEISA-host lifecycle, not the meter. The meter-relevant subset:

- **Power Degraded** — individual phase loss, undervoltage, etc.
- **Power Loss** — running on backup power

These map cleanly to a Homie alarm/event capability on the utility-meter device. Other GEISA status items (CPU, memory, app-keepalive) are GEISA-host plumbing; they don't belong on an eBus utility-meter unless the meter itself is the GEISA host.

Additional events that aren't in GEISA but a utility meter typically publishes, which we should reserve slots for:

- Tamper / case-open
- Reverse-energy flag
- Time-sync state (PTP/NTP lock, drift)
- Outage / restoration timestamps with cause code where available
- Last-gasp / first-breath notifications (AMI)

## Open questions for the data-model draft

1. **Capability decomposition.** Three plausible Homie-node carvings of the above:
   (a) one big `meter` node with all properties flat (matches GEISA's single instantaneous message);
   (b) split per cadence — `meter-realtime` (≥1 Hz) / `meter-billing` (summation+demand) / `meter-events` (status);
   (c) split per audience — `energy` / `power` / `power-quality` / `nameplate` / `events`.
   The framework's design principle "Homie nodes represent capabilities" pushes toward (c).
2. **Per-phase representation.** GEISA repeats per-phase blocks in the protobuf. Homie has no protobuf — we can either (i) use Homie property name conventions like `voltage-a / voltage-b / voltage-c`, or (ii) model phases as child devices under the meter parent. Distribution-enclosure precedent should inform this.
3. **Quadrant-quadrant arithmetic.** The 47-field billing axis is largely combinations of a smaller orthogonal set. Worth deciding whether the data-model exposes the full axis (closer to GEISA, easier proxy mapping) or the orthogonal primitives plus computed views.
4. **Arithmetic vs. vectorial.** GEISA picks one stream per host via discovery. eBus could do the same (a nameplate property `calculation-convention: arithmetic | vectorial`), or expose both side-by-side where the meter provides them.
5. **Time fields.** GEISA uses µs UNIX epoch in the messages and ms UNIX epoch in the discovery API. eBus payload-format decisions land here.
6. **CT / PT ratios.** Not in the GEISA list, but real revenue meters publish CT primary, CT secondary, PT primary, PT secondary so downstream consumers can sanity-check. Worth adding.
7. **Service multiplier / register multiplier.** Same rationale — utility-side metering practice, missing from the GEISA inventory.
8. **Demand reset / billing-cycle boundary semantics.** Needed if eBus consumers will read billing fields without being confused about what window they cover.

## Next step

Convert this inventory into the eBus data-model document at `data-models/utility-meter.md`, using the same Homie-device/Homie-capability framing as `distribution-enclosure.md`. Resolve question 1 (capability decomposition) first — that decision shapes the rest of the document.
