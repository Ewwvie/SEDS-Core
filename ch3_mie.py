from renderer import AtmosApp
import moderngl_window as mglw


FRAG = """
#version 330
in  vec2 uv;
out vec4 fragColor;

uniform vec2  u_res;
uniform float u_time;
uniform float u_time_of_day;

const float PLANET_R = 6371e3;
const float ATMOS_R  = 6471e3;

const vec3  BETA_RAY = vec3(5.8e-6, 13.5e-6, 33.1e-6);
const float H_RAY    = 8500.0;

const vec3  BETA_MIE = vec3(21e-6);
const float H_MIE    = 1200.0;
const float G        = 0.76;

const int   VIEW_STEPS = 16;
const int   SUN_STEPS  = 8;

vec2 raySphere(vec3 ro, vec3 rd, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float d = b*b - c;
    if (d < 0.0) return vec2(1e9, -1e9);
    float s = sqrt(d);
    return vec2(-b - s, -b + s);
}

float densityRay(vec3 p) {
    float altitude = length(p) - PLANET_R;
    return exp(-altitude / H_RAY);
}

float densityMie(vec3 p) {
    float altitude = length(p) - PLANET_R;
    return exp(-altitude / H_MIE);
}

vec2 opticalDepth(vec3 ro, vec3 rd, float dist) {
    float stepSize = dist / float(SUN_STEPS);
    float odRay = 0.0;
    float odMie = 0.0;
    for (int i = 0; i < SUN_STEPS; i++) {
        vec3 p = ro + rd * (float(i) + 0.5) * stepSize;
        odRay += densityRay(p) * stepSize;
        odMie += densityMie(p) * stepSize;
    }
    return vec2(odRay, odMie);
}

float phaseRayleigh(float cosTheta) {
    return (3.0 / (16.0 * 3.14159265)) * (1.0 + cosTheta * cosTheta);
}

float phaseMie(float cosTheta) {
    float g2 = G * G;
    float denom = 1.0 + g2 - 2.0 * G * cosTheta;
    return (1.0 - g2) / (4.0 * 3.14159265 * pow(denom, 1.5));
}

vec3 calcScattering(vec3 ro, vec3 rd, vec3 sunDir) {
    vec2 hit = raySphere(ro, rd, ATMOS_R);
    if (hit.x > hit.y) return vec3(0.0);

    float tStart   = max(hit.x, 0.0);
    float tEnd     = hit.y;
    float stepSize = (tEnd - tStart) / float(VIEW_STEPS);
    float cosTheta = dot(rd, sunDir);

    float pRay = phaseRayleigh(cosTheta);
    float pMie = phaseMie(cosTheta);

    vec3 totalRay = vec3(0.0);
    vec3 totalMie = vec3(0.0);

    for (int i = 0; i < VIEW_STEPS; i++) {
        vec3 pos = ro + rd * (tStart + (float(i) + 0.5) * stepSize);

        vec2 od_cam = opticalDepth(ro, rd, tStart + float(i) * stepSize);
        vec2 sunHit = raySphere(pos, sunDir, ATMOS_R);
        vec2 od_sun = opticalDepth(pos, sunDir, sunHit.y);

        vec3 T = exp(-BETA_RAY * (od_cam.x + od_sun.x)
                     -BETA_MIE * (od_cam.y + od_sun.y));

        totalRay += T * densityRay(pos) * BETA_RAY * pRay * stepSize;
        totalMie += T * densityMie(pos) * BETA_MIE * pMie * stepSize;
    }

    return (totalRay + totalMie) * 22.0;
}

void main() {
    float aspect = u_res.x / u_res.y;
    vec3 ro     = vec3(0.0, PLANET_R + 100.0, 0.0);
    vec3 rd     = normalize(vec3(uv.x * aspect, uv.y + 0.1, -1.5));

    float angle = (u_time_of_day - 0.5) * 3.14159265;
    vec3 sunDir = normalize(vec3(0.0, sin(angle), -cos(angle)));

    vec3 col = calcScattering(ro, rd, sunDir);

    float sunDisk = smoothstep(0.9995, 1.0, dot(rd, sunDir));
    col += vec3(1.0, 0.95, 0.8) * sunDisk * 2.0;

    col = 1.0 - exp(-col);
    col = pow(max(col, 0.0), vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
"""

class Ch3(AtmosApp):
    title = "Ch3: Mie Scattering"
    frag_shader = FRAG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_of_day = 0.5

    def render(self, time, frame_time):
        self.ctx.clear()
        if 'u_res' in self.prog:
            self.prog['u_res'].value = self.window_size
        if 'u_time' in self.prog:
            self.prog['u_time'].value = time
        self.prog['u_time_of_day'].value = self.time_of_day
        self.vao.render()

    def key_event(self, key, action, modifiers):
     keys = self.wnd.keys
     if action != keys.ACTION_PRESS:
        return
     step = 0.02
     if key == keys.RIGHT:
        self.time_of_day = min(1.0, self.time_of_day + step)
     elif key == keys.LEFT:
        self.time_of_day = max(0.0, self.time_of_day - step)
     print(f"time_of_day = {self.time_of_day:.2f}")
if __name__ == "__main__":
    mglw.run_window_config(Ch3)