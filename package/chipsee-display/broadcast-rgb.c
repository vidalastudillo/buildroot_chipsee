/*
 * Dump connector properties (values + enum names) and set output_format=RGB,
 * Broadcast RGB=Limited 16:235 via legacy DRM_IOCTL_MODE_SETPROPERTY.
 */
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>

#ifndef DRM_MODE_OBJECT_CONNECTOR
#define DRM_MODE_OBJECT_CONNECTOR 0xedcbedcb
#endif

/* Print all properties of an object; return prop_id matching name */
static uint32_t dump_props(int fd, uint32_t obj_id, uint32_t obj_type,
                            const char *find_name, uint64_t *find_val)
{
    struct drm_mode_obj_get_properties op = { .obj_id = obj_id, .obj_type = obj_type };
    if (ioctl(fd, DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &op) || !op.count_props) return 0;
    uint32_t n = op.count_props;
    uint32_t *ids  = calloc(n, sizeof(*ids));
    uint64_t *vals = calloc(n, sizeof(*vals));
    op.props_ptr = (uintptr_t)ids; op.prop_values_ptr = (uintptr_t)vals; op.count_props = n;
    ioctl(fd, DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &op);

    uint32_t result = 0;
    for (uint32_t i = 0; i < op.count_props; i++) {
        struct drm_mode_get_property gp = { .prop_id = ids[i] };
        if (ioctl(fd, DRM_IOCTL_MODE_GETPROPERTY, &gp)) continue;

        /* get enum names if it's an enum property */
        char enum_name[64] = "";
        if ((gp.flags & DRM_MODE_PROP_ENUM) && gp.count_enum_blobs) {
            uint32_t ne = gp.count_enum_blobs;
            struct drm_mode_property_enum *enums = calloc(ne, sizeof(*enums));
            gp.enum_blob_ptr = (uintptr_t)enums; gp.count_enum_blobs = ne;
            if (!ioctl(fd, DRM_IOCTL_MODE_GETPROPERTY, &gp)) {
                for (uint32_t e = 0; e < ne; e++)
                    if (enums[e].value == vals[i]) {
                        snprintf(enum_name, sizeof(enum_name), " [%s]", enums[e].name);
                        break;
                    }
            }
            free(enums);
        }
        fprintf(stderr, "  prop[%u] id=%u name='%s' val=%llu%s\n",
                i, ids[i], gp.name, (unsigned long long)vals[i], enum_name);
        if (find_name && !strcmp(gp.name, find_name)) {
            if (find_val) *find_val = vals[i];
            result = ids[i];
        }
    }
    free(ids); free(vals);
    return result;
}

static int set_prop(int fd, uint32_t obj_id, uint32_t prop_id, uint64_t val)
{
    struct drm_mode_connector_set_property sp = {
        .value       = val,
        .prop_id     = prop_id,
        .connector_id = obj_id,
    };
    return ioctl(fd, DRM_IOCTL_MODE_SETPROPERTY, &sp);
}

int main(void)
{
    int fd = open("/dev/dri/card1", O_RDWR);
    if (fd < 0) { perror("open"); return 1; }
    ioctl(fd, DRM_IOCTL_DROP_MASTER, 0); /* clear stale master if any */
    if (ioctl(fd, DRM_IOCTL_SET_MASTER, 0)) perror("SET_MASTER (continuing)");

    uint32_t conn_ids[8] = {0};
    struct drm_mode_card_res res = {
        .connector_id_ptr = (uintptr_t)conn_ids, .count_connectors = 8,
    };
    ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res);

    /* find connected connector */
    uint32_t conn_id = 0;
    for (uint32_t c = 0; c < res.count_connectors && !conn_id; c++) {
        struct drm_mode_get_connector co = { .connector_id = conn_ids[c] };
        ioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &co);
        if (co.connection == 1) conn_id = conn_ids[c];
    }
    fprintf(stderr, "connector=%u\n", conn_id);
    if (!conn_id) { fprintf(stderr, "no connector\n"); return 1; }

    fprintf(stderr, "--- connector properties ---\n");
    uint64_t of_val = 0, br_val = 0;
    uint32_t of_prop = dump_props(fd, conn_id, DRM_MODE_OBJECT_CONNECTOR, "output_format", &of_val);
    uint32_t br_prop = dump_props(fd, conn_id, DRM_MODE_OBJECT_CONNECTOR, "Broadcast RGB",  &br_val);
    /* dump_props already printed everything; just re-fetch IDs above */

    fprintf(stderr, "output_format prop=%u val=%llu  Broadcast_RGB prop=%u val=%llu\n",
            of_prop, (unsigned long long)of_val, br_prop, (unsigned long long)br_val);

    /* Set output_format=0 (RGB) if not already */
    if (of_prop && of_val != 0) {
        if (set_prop(fd, conn_id, of_prop, 0))
            perror("SET output_format");
        else
            fprintf(stderr, "output_format set to 0 (RGB)\n");
    }
    /* Set Broadcast RGB=2 (Limited 16:235) — bridge expects limited range */
    if (br_prop && br_val != 2) {
        if (set_prop(fd, conn_id, br_prop, 2))
            perror("SET Broadcast RGB");
        else
            fprintf(stderr, "Broadcast RGB set to 2 (Limited 16:235)\n");
    }

    printf("done\n");
    ioctl(fd, DRM_IOCTL_DROP_MASTER, 0);
    close(fd);
    return 0;
}
