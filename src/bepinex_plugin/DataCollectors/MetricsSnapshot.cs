using System.Collections.Generic;
using Newtonsoft.Json;

namespace DysonMCP
{
    /// <summary>
    /// Complete metrics snapshot for all planets at a point in time.
    /// </summary>
    public class MetricsSnapshot
    {
        [JsonProperty("timestamp")]
        public long Timestamp { get; set; }

        [JsonProperty("gameTick")]
        public long GameTick { get; set; }

        [JsonProperty("planets")]
        public Dictionary<int, PlanetMetrics> Planets { get; set; }

        public MetricsSnapshot()
        {
            Planets = new Dictionary<int, PlanetMetrics>();
        }
    }

    /// <summary>
    /// Metrics for a single planet.
    /// </summary>
    public class PlanetMetrics
    {
        [JsonProperty("planetId")]
        public int PlanetId { get; set; }

        [JsonProperty("planetName")]
        public string PlanetName { get; set; }

        [JsonProperty("power")]
        public PowerMetrics Power { get; set; }

        [JsonProperty("production")]
        public List<ProductionMetric> Production { get; set; }

        [JsonProperty("belts")]
        public List<BeltMetric> Belts { get; set; }

        public PlanetMetrics()
        {
            Production = new List<ProductionMetric>();
            Belts = new List<BeltMetric>();
        }
    }

    /// <summary>
    /// Power grid metrics for a planet.
    /// </summary>
    public class PowerMetrics
    {
        [JsonProperty("generationEnergyPerTick")]
        public long GenerationEnergyPerTick { get; set; }

        [JsonProperty("consumptionEnergyPerTick")]
        public long ConsumptionEnergyPerTick { get; set; }

        [JsonProperty("surplusEnergyPerTick")]
        public long SurplusEnergyPerTick => GenerationEnergyPerTick - ConsumptionEnergyPerTick;

        /// <summary>
        /// Power generation in MW (for display).
        /// DSP uses 60 ticks per second, energy is in Joules per tick.
        /// </summary>
        [JsonProperty("generationMW")]
        public double GenerationMW => GenerationEnergyPerTick * 60.0 / 1_000_000.0;

        /// <summary>
        /// Power consumption in MW (for display).
        /// </summary>
        [JsonProperty("consumptionMW")]
        public double ConsumptionMW => ConsumptionEnergyPerTick * 60.0 / 1_000_000.0;

        /// <summary>
        /// Power surplus in MW (for display).
        /// </summary>
        [JsonProperty("surplusMW")]
        public double SurplusMW => GenerationMW - ConsumptionMW;

        [JsonProperty("accumulatorCurrentEnergy")]
        public long AccumulatorCurrentEnergy { get; set; }

        [JsonProperty("accumulatorMaxEnergy")]
        public long AccumulatorMaxEnergy { get; set; }

        /// <summary>
        /// Accumulator charge percentage (0-100).
        /// </summary>
        [JsonProperty("accumulatorPercent")]
        public double AccumulatorPercent =>
            AccumulatorMaxEnergy > 0
                ? (double)AccumulatorCurrentEnergy / AccumulatorMaxEnergy * 100.0
                : 0.0;

        [JsonProperty("generatorCount")]
        public int GeneratorCount { get; set; }

        [JsonProperty("consumerCount")]
        public int ConsumerCount { get; set; }

        [JsonProperty("accumulatorCount")]
        public int AccumulatorCount { get; set; }
    }

    /// <summary>
    /// Production metrics for an assembler/smelter.
    /// </summary>
    public class ProductionMetric
    {
        [JsonProperty("assemblerId")]
        public int AssemblerId { get; set; }

        [JsonProperty("recipeId")]
        public int RecipeId { get; set; }

        [JsonProperty("protoId")]
        public int ProtoId { get; set; }

        /// <summary>
        /// Number of items produced in the last collection period.
        /// </summary>
        [JsonProperty("itemsProduced")]
        public int ItemsProduced { get; set; }

        /// <summary>
        /// Calculated production rate in items per minute.
        /// </summary>
        [JsonProperty("productionRate")]
        public double ProductionRate { get; set; }

        /// <summary>
        /// True if input slots are empty (starved for input).
        /// </summary>
        [JsonProperty("inputStarved")]
        public bool InputStarved { get; set; }

        /// <summary>
        /// True if output slots are full (backed up).
        /// </summary>
        [JsonProperty("outputBlocked")]
        public bool OutputBlocked { get; set; }

        /// <summary>
        /// Current power level (0-1).
        /// </summary>
        [JsonProperty("powerLevel")]
        public float PowerLevel { get; set; }
    }

    /// <summary>
    /// Belt throughput metrics.
    /// </summary>
    public class BeltMetric
    {
        [JsonProperty("beltId")]
        public int BeltId { get; set; }

        /// <summary>
        /// Item type being carried (item proto ID).
        /// </summary>
        [JsonProperty("itemType")]
        public int ItemType { get; set; }

        /// <summary>
        /// Current throughput in items per second.
        /// </summary>
        [JsonProperty("throughput")]
        public float Throughput { get; set; }

        /// <summary>
        /// Maximum throughput based on belt tier.
        /// Mk1: 6/s, Mk2: 12/s, Mk3: 30/s
        /// </summary>
        [JsonProperty("maxThroughput")]
        public float MaxThroughput { get; set; }

        /// <summary>
        /// Belt saturation percentage (0-100).
        /// </summary>
        [JsonProperty("saturationPercent")]
        public double SaturationPercent =>
            MaxThroughput > 0
                ? Throughput / MaxThroughput * 100.0
                : 0.0;

        /// <summary>
        /// Number of items currently on the belt.
        /// </summary>
        [JsonProperty("itemCount")]
        public int ItemCount { get; set; }

        /// <summary>
        /// Belt buffer length.
        /// </summary>
        [JsonProperty("bufferLength")]
        public int BufferLength { get; set; }
    }

    /// <summary>
    /// Accumulated production data for rate calculation.
    /// </summary>
    public class ProductionAccumulator
    {
        public int RecipeId { get; set; }
        public int AssemblerId { get; set; }
        public int PlanetId { get; set; }
        public int TotalProduced { get; set; }
        public long FirstTick { get; set; }
        public long LastTick { get; set; }
        public bool InputStarved { get; set; }
        public bool OutputBlocked { get; set; }
        public float LastPowerLevel { get; set; }

        /// <summary>
        /// Calculate items per minute from accumulated data.
        /// </summary>
        public double CalculateRate()
        {
            if (LastTick <= FirstTick) return 0;
            // 60 ticks per second, 60 seconds per minute
            double ticksElapsed = LastTick - FirstTick;
            double minutesElapsed = ticksElapsed / (60.0 * 60.0);
            return minutesElapsed > 0 ? TotalProduced / minutesElapsed : 0;
        }
    }

    /// <summary>
    /// Accumulated power data for a planet.
    /// </summary>
    public class PowerAccumulator
    {
        public int PlanetId { get; set; }
        public long TotalGeneration { get; set; }
        public long TotalConsumption { get; set; }
        public long AccumulatorCurrent { get; set; }
        public long AccumulatorMax { get; set; }
        public int GeneratorCount { get; set; }
        public int ConsumerCount { get; set; }
        public int AccumulatorCount { get; set; }
        public long LastUpdateTick { get; set; }
    }

    /// <summary>
    /// Accumulated belt data for throughput calculation.
    /// </summary>
    public class BeltAccumulator
    {
        public int BeltId { get; set; }
        public int PlanetId { get; set; }
        public int ItemType { get; set; }
        public int TotalItems { get; set; }
        public int SampleCount { get; set; }
        public float MaxThroughput { get; set; }
        public int BufferLength { get; set; }
        public long FirstTick { get; set; }
        public long LastTick { get; set; }

        /// <summary>
        /// Calculate items per second from accumulated data.
        /// </summary>
        public float CalculateThroughput()
        {
            if (SampleCount <= 0) return 0;
            // Average items per sample, then convert to per-second
            return (float)TotalItems / SampleCount;
        }
    }
}
