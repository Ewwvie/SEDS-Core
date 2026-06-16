from renderer import AtmosApp
import moderngl_window as mglw

FRAG = """
#version 330
in  vec2 uv;
out vec4 fragColor;

uniform vec2  u_res;
uniform float u_time;

const float PLANET_R = 6371e3;
const float ATMOS_R  = 6471e3;
const vec3  BETA_RAY = vec3(5.8e-6, 13.5e-6, 33.1e-6);
const float H_RAY    = 8500.0;
const int   VIEW_STEPS = 16;
const int   SUN_STEPS  = 8;

// Ray-sphere intersection, returns (t_near, t_far)
vec2 raySphere(vec3 ro, vec3 rd, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float d = b*b - c;
    if (d < 0.0) return vec2(1e9, -1e9);
    float s = sqrt(d);
    return vec2(-b - s, -b + s);
}

// Air density drops exponentially with altitude
float density(vec3 p) {
    float altitude = length(p) - PLANET_R;
    return exp(-altitude / H_RAY);
}

// OPTICAL DEPTH: march along ray, sum up density at each step (Riemann sum)
float opticalDepth(vec3 ro, vec3 rd, float dist) {
    float stepSize = dist / float(SUN_STEPS);
    float total = 0.0;
    for (int i = 0; i < SUN_STEPS; i++) {
        vec3 p = ro + rd * (float(i) + 0.5) * stepSize;
        total += density(p) * stepSize;
    }
    return total;
}

// Rayleigh phase function — equation (1) from the assignment
float phaseRayleigh(float cosTheta) {
    return (3.0 / (16.0 * 3.14159265)) * (1.0 + cosTheta * cosTheta);
}

vec3 calcScattering(vec3 ro, vec3 rd, vec3 sunDir) {
    vec2 hit = raySphere(ro, rd, ATMOS_R);
    if (hit.x > hit.y) return vec3(0.0);

    float tStart   = max(hit.x, 0.0);
    float tEnd     = hit.y;
    float stepSize = (tEnd - tStart) / float(VIEW_STEPS);
    float cosTheta = dot(rd, sunDir);
    float phase    = phaseRayleigh(cosTheta);
    vec3  total    = vec3(0.0);

    for (int i = 0; i < VIEW_STEPS; i++) {
        vec3 pos = ro + rd * (tStart + (float(i) + 0.5) * stepSize);

        // Optical depth: camera → sample point
        float od_cam = opticalDepth(ro, rd, tStart + float(i) * stepSize);

        // Optical depth: sample point → sun
        vec2  sunHit = raySphere(pos, sunDir, ATMOS_R);
        float od_sun = opticalDepth(pos, sunDir, sunHit.y);

        // Beer-Lambert transmittance on both paths
        vec3 T = exp(-BETA_RAY * (od_cam + od_sun));

        total += T * density(pos) * BETA_RAY * phase * stepSize;
    }

    return total * 22.0;
}

void main() {
    float aspect = u_res.x / u_res.y;
    vec3 ro = vec3(0.0, PLANET_R + 100.0, 0.0);
    vec3 rd = normalize(vec3(uv.x * aspect, uv.y + 0.1, -1.5));

    // Try changing the y value: -0.1 = sunset, 0.5 = afternoon, 1.0 = noon
    vec3 sunDir = normalize(vec3(0.0, 0.1, -1.0));

    vec3 col = calcScattering(ro, rd, sunDir);
    col = 1.0 - exp(-col);
    col = pow(max(col, 0.0), vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
"""

class Ch1(AtmosApp):
    title = "Ch1: Rayleigh Scattering & Transmittance"
    frag_shader = FRAG

if __name__ == "__main__":
    mglw.run_window_config(Ch1)